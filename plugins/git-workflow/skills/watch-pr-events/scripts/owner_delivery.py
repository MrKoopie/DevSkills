"""Deliver through the existing chat owner without taking or releasing its writer."""

import json
import time
import uuid
from pathlib import Path


def observe(path, marker):
    """Bind the unique delivered user message to its surrounding turn lifecycle."""
    turn = None
    matched = None
    started = None
    with Path(path).open() as file:
        for line in file:
            try:
                item = json.loads(line)
            except ValueError:
                continue
            p = item.get("payload", {})
            if item.get("type") == "event_msg" and p.get("type") == "task_started":
                turn = p.get("turn_id")
                started = item.get("timestamp")
            if (
                item.get("type") == "response_item"
                and p.get("type") == "message"
                and p.get("role") == "user"
            ):
                if any(marker in c.get("text", "") for c in p.get("content", [])):
                    matched = turn
            if (
                matched
                and item.get("type") == "event_msg"
                and p.get("turn_id") == matched
            ):
                if p.get("type") == "turn_aborted":
                    raise RuntimeError("Owner continuation was aborted; do not requeue")
                if p.get("type") == "task_complete":
                    return {
                        "turn_id": matched,
                        "started_at": started,
                        "completed_at": item.get("timestamp"),
                        "last_agent_message": p.get("last_agent_message", ""),
                    }
    return {"turn_id": matched, "started_at": started} if matched else None


def deliver(rpc, state, message, record, path, write_receipt):
    """Queue exactly once; acknowledgement is never treated as turn completion."""
    if time.time() >= state["deadline"]:
        raise RuntimeError("Original watch deadline expired before owner queueing")
    marker = "WATCH_DELIVERY_" + uuid.uuid4().hex
    client_id = str(uuid.uuid4())
    record.update(
        status="queue_pending",
        route="owner_queue",
        client_user_message_id=client_id,
        marker=marker,
    )
    write_receipt(path, record)
    if time.time() >= state["deadline"]:
        raise RuntimeError("Original watch deadline expired before owner queueing")
    # Persist queue intent before the request; a lost reply must never cause a duplicate enqueue.
    result = rpc.call(
        "thread/queue/add",
        {
            "threadId": state["thread"],
            "clientUserMessageId": client_id,
            "input": [
                {"type": "text", "text": message + "\nDelivery reference: " + marker}
            ],
        },
    )
    record.update(
        status="queued_for_owner",
        queued_submission_id=result["queuedSubmission"]["id"],
        queued_at=time.time(),
    )
    write_receipt(path, record)
    while time.time() < state["deadline"]:
        thread = rpc.call(
            "thread/read", {"threadId": state["thread"], "includeTurns": False}
        )["thread"]
        if thread["id"] != state["thread"] or not thread.get("path"):
            raise RuntimeError("Wrong owner thread")
        evidence = observe(thread["path"], marker)
        if evidence:
            if record.get("turn_id") != evidence["turn_id"]:
                record.update(
                    status="running",
                    turn_id=evidence["turn_id"],
                    started_at=evidence["started_at"],
                )
                write_receipt(path, record)
            if evidence.get("completed_at"):
                canary = "HOST_CONTINUATION_OK" in evidence.get(
                    "last_agent_message", ""
                )
                if state.get("canary") and not canary:
                    raise RuntimeError("Owner canary completed without marker")
                record.update(
                    status="completed",
                    completed_at=evidence["completed_at"],
                    canary_verified=canary,
                )
                write_receipt(path, record)
                if state.get("canary"):
                    write_receipt(path.with_suffix(".canary.json"), record)
                return "Existing chat owner completed turn " + evidence["turn_id"]
        time.sleep(min(2, max(0, state["deadline"] - time.time())))
    cleanup = rpc.call(
        "thread/queue/delete",
        {
            "threadId": state["thread"],
            "queuedSubmissionId": record["queued_submission_id"],
        },
    )
    if not isinstance(cleanup, dict) or not isinstance(cleanup.get("deleted"), bool):
        raise RuntimeError(
            "Original deadline expired; could not confirm owner queue submission deletion"
        )
    deleted = cleanup["deleted"]
    record["queued_submission_deleted"] = deleted
    write_receipt(path, record)
    if deleted:
        raise RuntimeError(
            "Original deadline expired; removed the pending owner queue submission"
        )
    raise RuntimeError(
        "Original deadline expired; owner queue submission was already absent; inspect the chat before retrying"
    )
