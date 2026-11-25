#!/usr/bin/env python3
"""Behavioral tests; no GitHub writes or live Codex notifications."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "watch", Path(__file__).with_name("watch.py")
)
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def snapshot(status="in_progress", head="a", feedback=None):
    return {
        "head": head,
        "open": True,
        "feedback": feedback or {},
        "expected_workflows": ["CI"],
        "runs": {
            "1": {"name": "CI", "attempt": 1, "status": status, "conclusion": None}
        },
    }


class WatchTest(unittest.TestCase):
    def test_continuation_routes_both_providers_to_git_workflow_feedback(self):
        for provider in ("github", "gitlab"):
            with self.subTest(provider=provider):
                state = {
                    "provider": provider,
                    "host": "gitlab.example.com",
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "owning-chat",
                    "state_path": "/tmp/watch.json",
                    "snapshot": snapshot(),
                    "until_ready": True,
                    "delivery": "daemon",
                }
                with patch("daemon_delivery.deliver") as deliver:
                    w.notify(state, {"kind": "feedback"})
                message = deliver.call_args.args[1]
                self.assertIn("git-workflow:process-pr-feedback", message)
                self.assertIn("git-workflow:watch-pr-events", message)
                self.assertIn("do not run watch.py resume", message)

    def test_packaged_cli_recognizes_a_running_standalone_worker(self):
        state = {"pid": 123, "state_path": "/home/user/.codex/pr-watches/watch.json"}
        launcher = "/usr/bin/python3 /home/user/with spaces/.codex/skills/watch-pr-events/scripts/watch.py"
        with patch.object(
            w, "command", return_value=f'{launcher} run --state {state["state_path"]}\n'
        ):
            self.assertTrue(w.alive(state))
        with patch.object(
            w, "command", return_value=f"{launcher} run --state /tmp/other.json\n"
        ):
            self.assertFalse(w.alive(state))

    def test_unfinished_github_watch_cannot_be_replaced_by_start(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            state = {
                "repo": "owner/repo",
                "number": 2,
                "thread": "owning-chat",
                "status": "delivery_uncertain",
                "state_path": str(path),
                "deadline": 1000,
            }
            w.atomic(path, state)
            with (
                patch.object(
                    w.sys,
                    "argv",
                    [
                        "watch.py",
                        "start",
                        "--repo",
                        "owner/repo",
                        "--number",
                        "2",
                        "--thread",
                        "owning-chat",
                        "--state",
                        str(path),
                    ],
                ),
                patch.object(w, "alive", return_value=False),
                patch.object(w, "api") as api,
            ):
                with self.assertRaisesRegex(RuntimeError, "unfinished|unresolved"):
                    w.main()
            api.assert_not_called()
            self.assertEqual(json.loads(path.read_text()), state)

    def test_initially_ready_github_watch_reports_a_single_milestone(self):
        current = self.approved()
        event, candidate = w.detect(current, current, None)
        self.assertIsNone(event)
        self.assertIsNotNone(candidate)
        self.assertEqual(
            w.detect(current, current, candidate)[0]["kind"], "approved_and_green"
        )
        self.assertEqual(w.detect(current, current, None, candidate), (None, None))

    def test_slow_github_poll_cannot_deliver_after_the_original_deadline(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            w.atomic(
                path,
                {
                    "state_path": str(path),
                    "interval": 60,
                    "deadline": 1000,
                    "until_ready": True,
                    "delivery": "daemon",
                    "snapshot": snapshot(),
                },
            )
            now = 100

            def slow_read(_state):
                nonlocal now
                now = 1001
                return snapshot(feedback={"inline:2": "new"})

            with (
                patch.object(w.time, "time", side_effect=lambda: now),
                patch.object(w.time, "sleep"),
                patch.object(w.signal, "signal"),
                patch.object(w, "read_watch_snapshot", side_effect=slow_read),
                patch.object(w, "notify", return_value="unexpected delivery") as notify,
            ):
                w.run(path)
            notify.assert_not_called()
            self.assertEqual(json.loads(path.read_text())["status"], "expired")

    def test_default_start_continues_until_ready_and_one_shot_is_explicit(self):
        for extra, ongoing, timeout in [
            ([], True, 86400),
            (["--one-shot"], False, 7200),
            (["--until-ready"], True, 86400),
        ]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                with (
                    patch.object(
                        w.sys,
                        "argv",
                        [
                            "watch.py",
                            "start",
                            "--repo",
                            "owner/repo",
                            "--number",
                            "2",
                            "--thread",
                            "thread-id",
                            "--state",
                            str(path),
                            *extra,
                        ],
                    ),
                    patch.object(w, "api", return_value={"login": "me"}),
                    patch.object(w, "read_snapshot", return_value=snapshot()) as reader,
                    patch.object(w, "command", return_value="Usage: codex queue"),
                    patch.object(w.Path, "exists", side_effect=[False, True]),
                    patch.object(w.time, "time", return_value=100),
                    patch.object(
                        w.subprocess, "Popen", return_value=SimpleNamespace(pid=123)
                    ),
                    patch("builtins.print"),
                ):
                    w.main()
                result = json.loads(path.read_text())
                self.assertEqual(result["until_ready"], ongoing)
                self.assertEqual(result["delivery"], "daemon" if ongoing else "queue")
                self.assertEqual(result["deadline"], 100 + timeout)
                self.assertEqual(reader.call_args.args[-1], ongoing)

    def approved(self):
        result = snapshot("completed")
        result["runs"]["1"]["conclusion"] = "success"
        result["review_decision"] = "APPROVED"
        result["opinions"] = {
            "reviewer": {"id": 10, "state": "APPROVED", "commit_id": "a"}
        }
        return result

    def test_ready_requires_current_head_approval_and_nonempty_successful_workflows(
        self,
    ):
        good = self.approved()
        self.assertTrue(w.ready(good))
        cases = []
        stale = copy.deepcopy(good)
        stale["opinions"]["reviewer"]["commit_id"] = "old"
        cases.append(stale)
        for decision in ["REVIEW_REQUIRED", "CHANGES_REQUESTED", None]:
            bad = copy.deepcopy(good)
            bad["review_decision"] = decision
            cases.append(bad)
        for conclusion in ["failure", "cancelled", "skipped", "neutral", None]:
            bad = copy.deepcopy(good)
            bad["runs"]["1"]["conclusion"] = conclusion
            cases.append(bad)
        missing = copy.deepcopy(good)
        missing["expected_workflows"].append("Browser")
        cases.append(missing)
        empty = copy.deepcopy(good)
        empty["runs"] = {}
        cases.append(empty)
        pending = copy.deepcopy(good)
        pending["runs"]["1"]["status"] = "in_progress"
        cases.append(pending)
        rejected = copy.deepcopy(good)
        rejected["opinions"]["other"] = {"state": "CHANGES_REQUESTED", "commit_id": "a"}
        cases.append(rejected)
        for case in cases:
            self.assertFalse(w.ready(case), case)

    def test_new_successful_run_supersedes_old_failure_but_pending_new_run_does_not(
        self,
    ):
        current = self.approved()
        current["runs"]["1"]["conclusion"] = "failure"
        current["runs"]["2"] = {
            "name": "CI",
            "status": "completed",
            "conclusion": "success",
        }
        self.assertTrue(w.ready(current))
        current["runs"]["3"] = {"name": "CI", "status": "queued", "conclusion": None}
        self.assertFalse(w.ready(current))

    def test_completion_also_wakes_when_own_approval_changes_readiness(self):
        good = self.approved()
        event, candidate = w.detect(snapshot("completed"), good, None)
        self.assertIsNone(event)
        self.assertEqual(
            w.detect(snapshot("completed"), good, candidate)[0]["kind"],
            "approved_and_green",
        )
        good["open"] = False
        good["feedback"]["comment:1"] = "new"
        self.assertEqual(w.detect(snapshot(), good, None)[0]["kind"], "closed")

    def test_different_workflows_with_same_display_name_cannot_hide_failure(self):
        current = self.approved()
        current["runs"]["1"].update(workflow_id=10, conclusion="failure")
        current["runs"]["2"] = {
            "name": "CI",
            "workflow_id": 11,
            "status": "completed",
            "conclusion": "success",
        }
        self.assertFalse(w.ready(current))
        current["runs"]["3"] = {
            "name": "CI",
            "workflow_id": 10,
            "status": "completed",
            "conclusion": "success",
        }
        self.assertTrue(w.ready(current))

    def test_start_refuses_to_silently_reuse_a_different_active_watch(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            w.atomic(
                path,
                {
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "thread-id",
                    "workflows": ["CI"],
                    "until_ready": False,
                    "state_path": str(path),
                },
            )
            with (
                patch.object(
                    w.sys,
                    "argv",
                    [
                        "watch.py",
                        "start",
                        "--state",
                        str(path),
                        "--repo",
                        "owner/repo",
                        "--number",
                        "2",
                        "--thread",
                        "thread-id",
                        "--workflow",
                        "CI",
                        "--until-ready",
                    ],
                ),
                patch.object(w, "alive", return_value=True),
                self.assertRaises(RuntimeError),
            ):
                w.main()

    def test_legacy_github_state_path_is_reused_without_a_provider_marker(self):
        with tempfile.TemporaryDirectory() as root:
            key = hashlib.sha256(b"owner/repo#2:thread-id").hexdigest()[:24]
            path = Path(root) / "pr-watches" / f"{key}.json"
            state = {
                "repo": "owner/repo",
                "number": 2,
                "thread": "thread-id",
                "pid": 123,
                "workflows": ["CI"],
                "until_ready": True,
                "deadline": 1000,
                "status": "watching",
                "state_path": str(path),
            }
            w.atomic(path, state)
            with (
                patch.object(
                    w.sys,
                    "argv",
                    [
                        "watch.py",
                        "start",
                        "--repo",
                        "owner/repo",
                        "--number",
                        "2",
                        "--thread",
                        "thread-id",
                        "--workflow",
                        "CI",
                    ],
                ),
                patch.dict(w.os.environ, CODEX_HOME=root),
                patch.object(w, "alive", return_value=True),
                patch.object(w, "command") as command,
                patch.object(w.subprocess, "Popen") as spawn,
                patch("builtins.print") as printed,
            ):
                w.main()
            result = json.loads(printed.call_args.args[0])
            self.assertTrue(result["already_running"])
            self.assertEqual(result["state_path"], str(path))
            self.assertEqual(json.loads(path.read_text()), state)
            command.assert_not_called()
            spawn.assert_not_called()

    def test_until_ready_snapshot_uses_review_gate_and_rejects_inconsistent_or_incomplete_reads(
        self,
    ):
        def api(endpoint, pages=False):
            if endpoint.endswith("/pulls/2"):
                return {"state": "open", "head": {"sha": "a"}}
            if "/actions/runs?" in endpoint:
                return [
                    {
                        "workflow_runs": [
                            {
                                "id": 1,
                                "head_sha": "a",
                                "name": "CI",
                                "status": "completed",
                                "conclusion": "success",
                            }
                        ]
                    }
                ]
            if "/reviews?" in endpoint:
                return [
                    [
                        {
                            "id": 2,
                            "user": {"login": "me"},
                            "state": "APPROVED",
                            "commit_id": "a",
                        }
                    ],
                    [
                        {
                            "id": 1,
                            "user": {"login": "me"},
                            "state": "CHANGES_REQUESTED",
                            "commit_id": "old",
                        }
                    ],
                ]
            return [[]]

        gate = {
            "data": {
                "repository": {
                    "pullRequest": {"headRefOid": "a", "reviewDecision": "APPROVED"}
                }
            }
        }
        with (
            patch.object(w, "api", side_effect=api),
            patch.object(w, "command", return_value=json.dumps(gate)),
        ):
            result = w.read_snapshot("owner/repo", 2, ["CI"], "me", True)
        self.assertTrue(w.ready(result))
        self.assertEqual(
            result["feedback"], {}
        )  # Own approval still informs readiness.
        for invalid in [
            {},
            {"errors": ["unavailable"]},
            {"data": {"repository": None}},
            {
                "data": {
                    "repository": {
                        "pullRequest": {
                            "headRefOid": "changed",
                            "reviewDecision": "APPROVED",
                        }
                    }
                }
            },
        ]:
            with (
                patch.object(w, "api", side_effect=api),
                patch.object(w, "command", return_value=json.dumps(invalid)),
                self.assertRaises(RuntimeError),
            ):
                w.read_snapshot("owner/repo", 2, ["CI"], "me", True)

    def resume(self, path, current):
        with (
            patch.object(w.sys, "argv", ["watch.py", "resume", "--state", str(path)]),
            patch.object(w, "alive", return_value=False),
            patch.object(w, "read_snapshot", return_value=current),
            patch.object(w.time, "time", return_value=100),
            patch.object(
                w.subprocess, "Popen", return_value=SimpleNamespace(pid=123)
            ) as process,
            patch("builtins.print"),
        ):
            w.main()
        return json.loads(path.read_text()), process.call_count

    def test_multiple_resume_cycles_preserve_deadline_and_during_processing_events(
        self,
    ):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            baseline = snapshot()
            state = {
                "repo": "owner/repo",
                "number": 2,
                "thread": "thread-id",
                "actor": "me",
                "workflows": ["CI"],
                "interval": 60,
                "deadline": 1000,
                "until_ready": True,
                "state_path": str(path),
                "snapshot": baseline,
                "status": "queued",
                "cycles": 0,
                "resume_supported": False,
            }
            for cycle in range(1, 4):
                w.atomic(path, state)
                current = snapshot(feedback={f"inline:{cycle}": "new while processing"})
                resumed, spawned = self.resume(path, current)
                self.assertEqual(spawned, 1)
                self.assertEqual(resumed["deadline"], 1000)
                self.assertEqual(resumed["cycles"], cycle)
                self.assertEqual(resumed["snapshot"], baseline)
                self.assertEqual(
                    w.detect(resumed["snapshot"], current, None)[0]["kind"], "feedback"
                )
                # Simulate the next delivered event, then another processing turn.
                state = resumed
                baseline = current
                state.update(status="queued", snapshot=current)

    def test_resume_stops_at_ready_closed_or_original_deadline(self):
        for expected in ["complete", "closed", "expired"]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                current = self.approved() if expected == "complete" else snapshot()
                if expected == "closed":
                    current["open"] = False
                state = {
                    "repo": "owner/repo",
                    "number": 2,
                    "actor": "me",
                    "workflows": ["CI"],
                    "until_ready": True,
                    "status": "queued",
                    "deadline": 50 if expected == "expired" else 1000,
                    "state_path": str(path),
                    "stop_at_ready": True,
                    "event": (
                        {"kind": "approved_and_green"} if expected == "complete" else {}
                    ),
                    "snapshot": (
                        current if expected in ("complete", "closed") else snapshot()
                    ),
                }
                w.atomic(path, state)
                result, spawned = self.resume(path, current)
                self.assertEqual(result["status"], expected)
                self.assertEqual(spawned, 0)

    def test_uncertain_or_cancelled_delivery_cannot_be_automatically_resumed(self):
        for status in [
            "delivery_pending",
            "delivery_uncertain",
            "cancelled",
            "expired",
        ]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                w.atomic(
                    path,
                    {"until_ready": True, "status": status, "state_path": str(path)},
                )
                with self.assertRaises(RuntimeError):
                    self.resume(path, snapshot())

    def test_expired_resume_does_not_depend_on_github_availability(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            w.atomic(
                path,
                {
                    "until_ready": True,
                    "status": "queued",
                    "deadline": 1,
                    "state_path": str(path),
                },
            )
            with (
                patch.object(
                    w.sys, "argv", ["watch.py", "resume", "--state", str(path)]
                ),
                patch.object(w, "alive", return_value=False),
                patch.object(w.time, "time", return_value=100),
                patch.object(
                    w, "read_snapshot", side_effect=RuntimeError("API unavailable")
                ) as reader,
                patch("builtins.print"),
            ):
                w.main()
            reader.assert_not_called()
            self.assertEqual(json.loads(path.read_text())["status"], "expired")

    def test_live_delivery_process_cannot_be_mistaken_for_a_polling_waiter(self):
        for status in ["delivery_pending", "queued", "delivery_uncertain", "cancelled"]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                w.atomic(
                    path,
                    {"until_ready": True, "status": status, "state_path": str(path)},
                )
                with (
                    patch.object(
                        w.sys, "argv", ["watch.py", "resume", "--state", str(path)]
                    ),
                    patch.object(w, "alive", return_value=True),
                    self.assertRaises(RuntimeError),
                ):
                    w.main()
                with (
                    patch.object(
                        w.sys, "argv", ["watch.py", "status", "--state", str(path)]
                    ),
                    patch.object(w, "alive", return_value=True),
                    patch("builtins.print") as output,
                ):
                    w.main()
                result = json.loads(output.call_args.args[0])
                self.assertTrue(result["running"])
                self.assertFalse(result["waiting"])

    def test_new_pipeline_registration_clears_ready_candidate(self):
        good = self.approved()
        _, candidate = w.detect(snapshot(), good, None)
        late = copy.deepcopy(good)
        late["runs"]["2"] = {
            "name": "Browser",
            "workflow_id": 2,
            "status": "queued",
            "conclusion": None,
        }
        event, settled = w.detect(snapshot(), late, candidate)
        self.assertIsNone(event)
        self.assertIsNone(settled)

    def test_until_ready_notification_authorizes_only_existing_processing_loop(self):
        state = {
            "repo": "owner/repo",
            "number": 2,
            "thread": "thread-id",
            "snapshot": snapshot(),
            "state_path": "/tmp/state.json",
            "until_ready": True,
        }
        output = subprocess.CompletedProcess(
            [], 0, "Queued message id for thread thread-id.", ""
        )
        with patch.object(w.subprocess, "run", return_value=output) as process:
            w.notify(state, {"kind": "feedback", "body": "untrusted shell text"})
        message = process.call_args.args[0][5]
        self.assertIn("original deadline", message)
        self.assertNotIn("untrusted shell text", message)
        self.assertNotIn("Do not automatically re-arm", message)

    def test_completion_needs_a_nonempty_stable_current_head_set(self):
        before = snapshot()
        complete = snapshot("completed")
        event, candidate = w.detect(before, complete, None)
        self.assertIsNone(event)
        self.assertEqual(
            w.detect(before, complete, candidate)[0]["kind"], "pipelines_completed"
        )
        empty = snapshot()
        empty["runs"] = {}
        self.assertFalse(w.all_complete(empty))
        missing = snapshot("completed")
        missing["expected_workflows"] = ["CI", "Browser"]
        self.assertFalse(w.all_complete(missing))

    def test_failures_and_cancellations_are_completed_not_passed(self):
        for conclusion in ["failure", "cancelled", "success", "skipped"]:
            after = snapshot("completed")
            after["runs"]["1"]["conclusion"] = conclusion
            _, candidate = w.detect(snapshot(), after, None)
            self.assertEqual(
                w.detect(snapshot(), after, candidate)[0]["runs"]["1"]["conclusion"],
                conclusion,
            )

    def test_existing_completed_runs_do_not_repeat_and_reruns_do_trigger(self):
        before = snapshot("completed")
        self.assertIsNone(w.detect(before, before, None)[0])
        after = copy.deepcopy(before)
        after["runs"]["1"]["attempt"] = 2
        _, candidate = w.detect(before, after, None)
        self.assertEqual(
            w.detect(before, after, candidate)[0]["kind"], "pipelines_completed"
        )

    def test_changed_head_cannot_reuse_a_completed_old_head(self):
        before = snapshot("completed")
        self.assertIsNone(w.detect(before, snapshot(head="b"), None)[0])
        after = snapshot("completed", head="b")
        _, candidate = w.detect(before, after, None)
        self.assertEqual(
            w.detect(before, after, candidate)[0]["kind"], "pipelines_completed"
        )

    def test_new_reply_and_mutable_summary_edits_trigger_once(self):
        before = snapshot(feedback={"comment:1": "old"})
        for values in [
            {"comment:1": "edited"},
            {"comment:1": "old", "inline:2": "new"},
        ]:
            after = snapshot(feedback=values)
            self.assertEqual(w.detect(before, after, None)[0]["kind"], "feedback")
            self.assertIsNone(w.detect(after, after, None)[0])

    def test_snapshot_reads_all_pages_and_filters_own_messages_and_workflows(self):
        own = {"id": 1, "user": {"login": "me"}, "body": "own"}
        reply = {"id": 2, "user": {"login": "reviewer"}, "body": "new"}
        calls = []

        def api(endpoint, pages=False):
            calls.append((endpoint, pages))
            if endpoint.endswith("/pulls/2"):
                return {"state": "open", "head": {"sha": "a"}}
            if "/actions/runs?" in endpoint:
                return [
                    {
                        "workflow_runs": [
                            {
                                "id": 1,
                                "head_sha": "a",
                                "name": "CI",
                                "status": "completed",
                            },
                            {
                                "id": 2,
                                "head_sha": "old",
                                "name": "CI",
                                "status": "in_progress",
                            },
                        ]
                    },
                    {
                        "workflow_runs": [
                            {
                                "id": 3,
                                "head_sha": "a",
                                "name": "Other",
                                "status": "in_progress",
                            }
                        ]
                    },
                ]
            if "/reviews?" in endpoint:
                return [
                    [
                        {
                            "id": 4,
                            "user": {"login": "reviewer"},
                            "body": "",
                            "state": "APPROVED",
                        }
                    ]
                ]
            if "/issues/" in endpoint:
                return [[own], [reply]]
            return [[]]

        with patch.object(w, "api", side_effect=api):
            result = w.read_snapshot("owner/repo", 2, ["CI"], "me")
        self.assertEqual(set(result["feedback"]), {"comment:2", "review:4"})
        self.assertEqual(set(result["runs"]), {"1"})
        self.assertTrue(w.all_complete(result))
        self.assertTrue(all(paged for endpoint, paged in calls if "?" in endpoint))

    def test_notification_uses_only_metadata_not_comment_bodies(self):
        state = {
            "repo": "owner/repo",
            "number": 2,
            "thread": "thread-id",
            "snapshot": snapshot(),
            "state_path": "/tmp/state.json",
            "resume_supported": False,
        }
        output = subprocess.CompletedProcess(
            [], 0, "Queued message id for thread thread-id.\n", ""
        )
        with patch.object(w.subprocess, "run", return_value=output) as run:
            self.assertIn(
                "Queued message",
                w.notify(state, {"kind": "feedback", "body": "untrusted shell text"}),
            )
        command = run.call_args.args[0]
        self.assertNotIn("untrusted shell text", " ".join(command))
        self.assertNotIn("--resume", command)

    def test_actions_reads_warning_annotations_on_latest_scoped_successful_run(self):
        def actions_api(endpoint, pages=False):
            if endpoint.endswith("/pulls/2"):
                return {"state": "open", "head": {"sha": "a"}}
            if "/actions/runs?" in endpoint:
                return [
                    {
                        "workflow_runs": [
                            {
                                "id": run,
                                "workflow_id": 44,
                                "check_suite_id": suite,
                                "head_sha": sha,
                                "name": name,
                                "status": "completed",
                                "conclusion": "success",
                            }
                            for run, suite, sha, name in [
                                (1, 10, "a", "CI"),
                                (2, 20, "a", "CI"),
                                (3, 30, "old", "CI"),
                                (4, 40, "a", "Other"),
                            ]
                        ]
                    }
                ]
            if "/check-suites/" in endpoint:
                self.assertIn("/check-suites/20/", endpoint)
                self.assertTrue(pages)
                return [
                    {
                        "check_runs": [
                            {
                                "id": 91,
                                "head_sha": "a",
                                "output": {"annotations_count": 3},
                            },
                            {
                                "id": 92,
                                "head_sha": "old",
                                "output": {"annotations_count": 1},
                            },
                            {
                                "id": 93,
                                "head_sha": "a",
                                "output": {"annotations_count": 0},
                            },
                        ]
                    }
                ]
            if "/annotations?" in endpoint:
                self.assertIn("/check-runs/91/", endpoint)
                self.assertTrue(pages)
                return [
                    [{"annotation_level": "notice", "message": "ordinary notice"}],
                    [
                        {
                            "annotation_level": "warning",
                            "message": "untrusted warning body",
                        },
                        {"annotation_level": "failure", "message": "ordinary error"},
                    ],
                ]
            return [[]]

        with patch.object(w, "api", side_effect=actions_api):
            result = w.read_snapshot("owner/repo", 2, ["CI"], "me")
        warning = result["ci_warnings"]["check:91"]
        self.assertEqual(
            (warning["run_id"], warning["check_id"], warning["count"]), ("2", 91, 1)
        )
        self.assertNotIn("untrusted warning body", json.dumps(result))
        self.assertEqual(result["runs"]["2"]["conclusion"], "success")

    def test_warning_delivery_preserves_readiness_and_deduplicates_across_unavailable_reads(
        self,
    ):
        initial = snapshot()
        clean = self.approved()
        warned = copy.deepcopy(clean)
        warned["ci_warnings"] = {
            "check:91": {
                "run_id": "1",
                "check_id": 91,
                "count": 1,
                "fingerprint": "previously unseen warning",
            }
        }
        closed = copy.deepcopy(clean)
        closed.update(open=False, merged=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            w.atomic(
                path,
                {
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "thread-id",
                    "actor": "me",
                    "until_ready": True,
                    "delivery": "daemon",
                    "interval": 0,
                    "deadline": 1000,
                    "workflows": ["CI"],
                    "state_path": str(path),
                    "snapshot": initial,
                },
            )
            received = []

            def deliver(_state, message):
                received.append((_state["event"]["kind"], message))
                return "local delivery"

            observed = [warned, warned, clean, warned, closed]
            with (
                patch.object(w.time, "time", return_value=100),
                patch.object(w.time, "sleep"),
                patch.object(w.signal, "signal"),
                patch.object(w, "read_snapshot", side_effect=observed),
                patch("daemon_delivery.deliver", side_effect=deliver),
            ):
                w.run(path)
            self.assertEqual(
                [kind for kind, _ in received],
                ["ci_warnings", "approved_and_green", "merged"],
            )
            self.assertIn("check run 91", received[0][1])
            self.assertIn("decide whether", received[0][1])
            self.assertEqual(json.loads(path.read_text())["deadline"], 1000)

    def test_resume_warning_is_not_success(self):
        state = {
            "repo": "owner/repo",
            "number": 2,
            "thread": "thread-id",
            "snapshot": snapshot(),
            "state_path": "/tmp/state.json",
            "resume_supported": True,
        }
        output = subprocess.CompletedProcess(
            [],
            0,
            "Queued message id for thread thread-id.",
            "Warning: failed to resume",
        )
        with (
            patch.object(w.subprocess, "run", return_value=output),
            self.assertRaises(RuntimeError),
        ):
            w.notify(state, {"kind": "feedback"})

    def test_api_errors_do_not_notify_and_delivery_timeouts_do_not_retry(self):
        for failing_delivery in [False, True]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                state = {
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "thread-id",
                    "actor": "me",
                    "workflows": ["CI"],
                    "interval": 5,
                    "deadline": 10,
                    "state_path": str(path),
                    "snapshot": snapshot(),
                }
                w.atomic(path, state)
                new = snapshot(feedback={"inline:1": "new"})
                now = 0

                def sleep(interval):
                    nonlocal now
                    now += interval

                reader = new if failing_delivery else RuntimeError("unavailable")
                with (
                    patch.object(w.time, "time", side_effect=lambda: now),
                    patch.object(w.time, "sleep", side_effect=sleep),
                    patch.object(w.signal, "signal"),
                    patch.object(
                        w,
                        "read_snapshot",
                        side_effect=reader if isinstance(reader, Exception) else None,
                        return_value=new,
                    ),
                    patch.object(
                        w, "notify", side_effect=subprocess.TimeoutExpired("codex", 40)
                    ) as notify,
                ):
                    w.run(path)
                result = json.loads(path.read_text())
                self.assertEqual(
                    result["status"],
                    "delivery_uncertain" if failing_delivery else "expired",
                )
                self.assertEqual(notify.call_count, 1 if failing_delivery else 0)

    def test_ready_does_not_repeat_and_new_feedback_still_triggers(self):
        good = self.approved()
        reported_ready = w.readiness_signature(good)
        self.assertEqual(w.detect(good, good, None, reported_ready), (None, None))
        changed = copy.deepcopy(good)
        changed["feedback"]["comment:42"] = "new"
        self.assertEqual(
            w.detect(good, changed, None, reported_ready)[0]["kind"], "feedback"
        )

    def test_merge_and_unmerged_closure_are_distinct_even_with_failed_ci(self):
        for merged, kind in [(True, "merged"), (False, "closed")]:
            closed = snapshot()
            closed.update(open=False, merged=merged, merge_commit_sha="merge-sha")
            event, _ = w.detect(self.approved(), closed, None)
            self.assertEqual(event["kind"], kind)
            self.assertEqual(event["merge_commit_sha"], "merge-sha")

    def test_closed_snapshot_uses_verified_pr_state_without_depending_on_ci(self):
        pull = {
            "state": "closed",
            "head": {"sha": "a"},
            "merged": True,
            "merged_at": "2026-11-07T11:00:00Z",
            "merge_commit_sha": "merge-sha",
        }
        with patch.object(w, "api", return_value=pull) as api:
            result = w.read_snapshot("owner/repo", 2, ["CI"], "me", True)
        self.assertEqual(api.call_count, 1)
        self.assertTrue(result["merged"])
        self.assertEqual(result["merge_commit_sha"], "merge-sha")

    def test_default_ready_resume_keeps_original_deadline_and_continues(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            good = self.approved()
            w.atomic(
                path,
                {
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "thread-id",
                    "actor": "me",
                    "until_ready": True,
                    "status": "queued",
                    "snapshot": good,
                    "deadline": 1000,
                    "workflows": ["CI"],
                    "state_path": str(path),
                    "resume_supported": False,
                },
            )
            result, spawned = self.resume(path, good)
            self.assertEqual(spawned, 1)
            self.assertEqual(result["status"], "starting")
            self.assertEqual(result["deadline"], 1000)

    def test_queue_resume_cannot_miss_a_merge_during_feedback_processing(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            closed = snapshot()
            closed.update(open=False, merged=True)
            w.atomic(
                path,
                {
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "thread-id",
                    "actor": "me",
                    "until_ready": True,
                    "status": "queued",
                    "snapshot": snapshot(),
                    "deadline": 1000,
                    "workflows": ["CI"],
                    "state_path": str(path),
                    "resume_supported": False,
                },
            )
            result, spawned = self.resume(path, closed)
            self.assertEqual(spawned, 1)
            self.assertTrue(result["snapshot"]["open"])

    def test_daemon_announces_ready_once_then_announces_final_state_and_exits(self):
        for merged, terminal in [(True, "merged"), (False, "closed")]:
            with tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                good = self.approved()
                closed = copy.deepcopy(good)
                closed.update(open=False, merged=merged)
                state = {
                    "repo": "owner/repo",
                    "number": 2,
                    "thread": "thread-id",
                    "actor": "me",
                    "until_ready": True,
                    "delivery": "daemon",
                    "interval": 0,
                    "deadline": 1000,
                    "workflows": ["CI"],
                    "state_path": str(path),
                    "snapshot": snapshot(),
                }
                w.atomic(path, state)
                with (
                    patch.object(w.time, "time", return_value=100),
                    patch.object(w.time, "sleep"),
                    patch.object(w.signal, "signal"),
                    patch.object(
                        w, "read_snapshot", side_effect=[good, good, good, good, closed]
                    ) as reader,
                    patch.object(
                        w, "notify", return_value="matching turn completed"
                    ) as notify,
                ):
                    w.run(path)
                self.assertEqual(
                    [c.args[1]["kind"] for c in notify.call_args_list],
                    ["approved_and_green", terminal],
                )
                self.assertEqual(reader.call_count, 5)
                result = json.loads(path.read_text())
                self.assertEqual(result["status"], terminal)
                self.assertEqual(result["deadline"], 1000)

    def test_terminal_notice_is_notification_only_and_does_not_rearm(self):
        state = {
            "repo": "owner/repo",
            "number": 2,
            "thread": "thread-id",
            "snapshot": snapshot(),
            "state_path": "/tmp/state.json",
            "until_ready": True,
        }
        output = subprocess.CompletedProcess(
            [], 0, "Queued message id for thread thread-id.", ""
        )
        for kind, label in [
            ("merged", "PR merged"),
            ("closed", "PR closed without merging"),
        ]:
            with patch.object(w.subprocess, "run", return_value=output) as process:
                w.notify(state, {"kind": kind})
            message = process.call_args.args[0][5]
            self.assertIn(label, message)
            self.assertIn("Do not re-arm", message)
            self.assertNotIn("process-pr-feedback", message)


if __name__ == "__main__":
    unittest.main()
