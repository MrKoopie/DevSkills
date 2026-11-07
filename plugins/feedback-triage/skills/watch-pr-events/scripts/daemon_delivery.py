"""Execute an authorized continuation on the host daemon, with a durable delivery receipt."""

import json
import socket
import time
import uuid
from pathlib import Path

from host_rpc import RPC, RPCError
from state_io import atomic_json as receipt


class NeedsInput(RuntimeError):
    pass


def history(path):
    """Read lifecycle markers and the most recent execution context, without guessing idleness."""
    context = None
    active = None
    with Path(path).open() as file:
        lines = file.readlines()
    for line in lines:
        try:
            item = json.loads(line)
        except ValueError:
            continue  # A concurrent writer may have a partial last line.
        payload = item.get("payload", {})
        if item.get("type") == "turn_context":
            context = payload
        if item.get("type") == "event_msg":
            if payload.get("type") == "task_started":
                active = payload.get("turn_id", "unknown")
            elif payload.get("type") in ("task_complete", "turn_aborted"):
                if active in (None, "unknown", payload.get("turn_id")):
                    active = None
    if context is None:
        raise RuntimeError("No saved execution context")
    return context, active


def resume_params(thread, context):
    """Recreate the saved restricted profile and approval routing, never full-access defaults."""
    profile = context.get("permission_profile", {})
    if (
        profile.get("type") != "managed"
        or profile.get("network") != "restricted"
        or profile.get("file_system", {}).get("type") != "restricted"
    ):
        raise RuntimeError(
            "Headless delivery requires a saved restricted managed permission profile"
        )
    filesystem = {}
    for rule in profile.get("file_system", {}).get("entries", []):
        path = rule["path"]
        target = path.get("value")
        if path["type"] == "special":
            target = ":" + target["kind"]
        elif path["type"] == "path":
            target = path.get("path")
            if not target or not Path(target).is_absolute():
                raise RuntimeError("Invalid saved filesystem path")
        else:
            raise RuntimeError("Unsupported saved filesystem rule")
        filesystem[target] = rule["access"]
    if not filesystem or not context.get("model") or not context.get("effort"):
        raise RuntimeError("Incomplete saved execution context")
    name = "watch_" + thread.replace("-", "_")
    return {
        "threadId": thread,
        "excludeTurns": True,
        "model": context["model"],
        "cwd": context["cwd"],
        "approvalPolicy": context["approval_policy"],
        "approvalsReviewer": context["approvals_reviewer"],
        "permissions": name,
        "config": {
            "model_reasoning_effort": context["effort"],
            "permissions": {
                name: {"filesystem": filesystem, "network": {"enabled": False}}
            },
        },
    }


def deliver(state, message):
    """Wait for the owning turn, then observe actual start and completion; never retry an uncertain start."""
    path = Path(state["state_path"]).with_suffix(".delivery.json")
    record = {
        "thread": state["thread"],
        "event": state.get("event", {}),
        "detected_at": time.time(),
        "status": "waiting_for_idle",
        "delivery": "daemon",
    }
    receipt(path, record)
    rpc = None
    started = False
    turn = None
    try:
        if time.time() >= state["deadline"]:
            raise RuntimeError("Original watch deadline expired before delivery")
        rpc = RPC(state["daemon_socket"])
        thread = rpc.call(
            "thread/read", {"threadId": state["thread"], "includeTurns": False}
        )["thread"]
        if thread["id"] != state["thread"] or not thread.get("path"):
            raise RuntimeError("Wrong daemon thread")
        while True:
            context, active = history(thread["path"])
            if not active and thread.get("status", {}).get("type") != "active":
                break
            if time.time() >= state["deadline"]:
                raise RuntimeError("Original watch deadline expired before delivery")
            time.sleep(2)
            thread = rpc.call(
                "thread/read", {"threadId": state["thread"], "includeTurns": False}
            )["thread"]
        params = resume_params(state["thread"], context)
        while True:
            try:
                resumed = rpc.call("thread/resume", params)
                break
            except RPCError as error:
                if error.code != -32600 or "active writer" not in error.message:
                    raise
                record.update(status="waiting_for_writer", last_wait_at=time.time())
                receipt(path, record)
                if time.time() >= state["deadline"]:
                    raise RuntimeError("Original deadline expired waiting for writer")
                time.sleep(2)
                context, active = history(thread["path"])
                if active:
                    continue
                params = resume_params(state["thread"], context)
        if (
            resumed["model"] != context["model"]
            or resumed["reasoningEffort"] != context["effort"]
            or resumed["cwd"] != context["cwd"]
            or resumed["approvalPolicy"] != context["approval_policy"]
            or resumed["approvalsReviewer"] != context["approvals_reviewer"]
            or resumed.get("activePermissionProfile", {}).get("id")
            != params["permissions"]
        ):
            raise RuntimeError(
                "Daemon did not preserve saved model/permissions/approval routing"
            )
        # Recheck the persisted lifecycle after loading to avoid stealing a desktop turn.
        if (
            history(thread["path"])[1]
            or resumed["thread"]["status"]["type"] == "active"
        ):
            raise RuntimeError("Owning thread became active during handoff")
        if time.time() >= state["deadline"]:
            raise RuntimeError("Original watch deadline expired before turn start")
        record.update(
            status="start_pending",
            model=resumed["model"],
            effort=resumed["reasoningEffort"],
            requested_at=time.time(),
        )
        receipt(path, record)
        # Set before sending: an interrupted request is uncertain, never safe to duplicate.
        started = True
        result = rpc.call(
            "turn/start",
            {
                "threadId": state["thread"],
                "clientUserMessageId": str(uuid.uuid4()),
                "input": [{"type": "text", "text": message}],
                "turnTrigger": "watch-pr-events",
            },
        )
        turn = result["turn"]["id"]
        record.update(status="accepted", turn_id=turn, accepted_at=time.time())
        receipt(path, record)
        canary_seen = False
        while True:
            if time.time() >= state["deadline"]:
                rpc.call(
                    "turn/interrupt", {"threadId": state["thread"], "turnId": turn}
                )
                raise NeedsInput("Original deadline reached during continuation")
            try:
                event = rpc.recv()
            except socket.timeout:
                continue
            if "method" in event and "id" in event:
                rpc.call(
                    "turn/interrupt", {"threadId": state["thread"], "turnId": turn}
                )
                raise NeedsInput(
                    "Headless turn requires interactive approval, input or unavailable client tools"
                )
            if event.get("method") == "item/completed":
                item = event.get("params", {}).get("item", {})
                if item.get(
                    "type"
                ) == "agentMessage" and "HOST_CONTINUATION_OK" in item.get("text", ""):
                    canary_seen = True
            if (
                event.get("method") == "turn/started"
                and event.get("params", {}).get("turn", {}).get("id") == turn
            ):
                record.update(status="running", started_at=time.time())
                receipt(path, record)
            if event.get("method") == "turn/completed":
                done = event.get("params", {}).get("turn", {})
                if done.get("id") != turn:
                    continue
                if done.get("status") != "completed":
                    raise NeedsInput("Headless continuation did not complete")
                if state.get("canary") and not canary_seen:
                    raise NeedsInput(
                        "Canary turn completed without the expected marker"
                    )
                record.update(
                    status="completed",
                    completed_at=time.time(),
                    canary_verified=canary_seen,
                )
                receipt(path, record)
                return f"Host daemon completed turn {turn}"
    except BaseException as error:
        record.update(
            status="needs_input"
            if isinstance(error, NeedsInput)
            else "delivery_uncertain"
            if started
            else "failed_before_start",
            error_type=type(error).__name__,
            failed_at=time.time(),
        )
        receipt(path, record)
        raise
    finally:
        if rpc:
            if turn and record.get("status") != "completed":
                try:
                    rpc.call(
                        "turn/interrupt", {"threadId": state["thread"], "turnId": turn}
                    )
                except (RuntimeError, OSError, EOFError):
                    pass
            try:
                rpc.call("thread/unsubscribe", {"threadId": state["thread"]})
            except (RuntimeError, OSError, EOFError):
                pass
            rpc.close()
