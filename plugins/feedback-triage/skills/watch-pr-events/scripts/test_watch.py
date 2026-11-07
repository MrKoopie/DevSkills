#!/usr/bin/env python3
"""Behavioral tests; no GitHub writes or live Codex notifications."""

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
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
        for policy in (
            {"until_ready": False},
            {"until_ready": True, "stop_at_ready": True},
        ):
            with self.subTest(policy=policy), tempfile.TemporaryDirectory() as root:
                path = Path(root) / "state.json"
                w.atomic(
                    path,
                    {
                        "repo": "owner/repo",
                        "number": 2,
                        "thread": "thread-id",
                        "workflows": ["CI"],
                        **policy,
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
                    "snapshot": current
                    if expected in ("complete", "closed")
                    else snapshot(),
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

    def test_daemon_notification_defers_resume_to_dispatcher(self):
        state = {
            "repo": "owner/repo",
            "number": 2,
            "thread": "thread-id",
            "snapshot": snapshot(),
            "state_path": "/tmp/state.json",
            "until_ready": True,
            "delivery": "daemon",
        }
        with patch("daemon_delivery.deliver", return_value="completed") as deliver:
            w.notify(state, {"kind": "feedback"})
        message = deliver.call_args.args[1]
        self.assertIn("host dispatcher resumes polling", message)
        self.assertIn("do not run watch.py resume", message)
        self.assertNotIn("run the skill resume command", message)
        self.assertIn("original deadline", message)

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
                    "interval": 0,
                    "deadline": 10,
                    "state_path": str(path),
                    "snapshot": snapshot(),
                }
                w.atomic(path, state)
                new = snapshot(feedback={"inline:1": "new"})
                clock = [0, 1, 1, 1, 1, 11] if not failing_delivery else [0, 1, 1, 1, 1]
                reader = new if failing_delivery else RuntimeError("unavailable")
                with (
                    patch.object(w.time, "time", side_effect=clock),
                    patch.object(w.time, "sleep"),
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
        self.assertIsNone(w.detect(good, good, None)[0])
        changed = copy.deepcopy(good)
        changed["feedback"]["comment:42"] = "new"
        self.assertEqual(w.detect(good, changed, None)[0]["kind"], "feedback")

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

    def test_failed_state_write_preserves_previous_json_and_removes_temporary_file(
        self,
    ):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            w.atomic(path, {"status": "watching"})
            with patch.object(w.json, "dump", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    w.atomic(path, {"status": "queued"})
            self.assertEqual(json.loads(path.read_text()), {"status": "watching"})
            self.assertEqual(list(Path(root).iterdir()), [path])

    def test_atomic_state_survives_a_write_during_another_write(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            real_dump = json.dump

            def interleaved(value, file, **options):
                if value == {"value": "outer"}:
                    w.atomic(path, {"value": "inner"})
                return real_dump(value, file, **options)

            with patch.object(w.json, "dump", side_effect=interleaved):
                w.atomic(path, {"value": "outer"})
            self.assertEqual(json.loads(path.read_text()), {"value": "outer"})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(list(Path(root).iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
