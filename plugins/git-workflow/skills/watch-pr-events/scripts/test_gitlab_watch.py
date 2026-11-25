#!/usr/bin/env python3
"""Controlled GitLab CLI and delivery responses."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import watch

HOST = "gitlab.example.com"
PROJECT = "group/subgroup/project"
NUMBER = 509
HEAD = "a" * 40
NEXT = "b" * 40
BASE = "c" * 40
SYNTHETIC = "d" * 40
MR = "projects/group%2Fsubgroup%2Fproject/merge_requests/509"
JOBS = "projects/71/pipelines/42/jobs?per_page=100"


def json_pages(*pages):
    return "\n".join(json.dumps(page, indent=2) for page in pages)


class GitLabResponses:
    def __init__(self):
        self.mr = {
            "iid": NUMBER,
            "sha": HEAD,
            "state": "opened",
            "detailed_merge_status": "ci_still_running",
            "diff_refs": {"head_sha": HEAD, "base_sha": BASE, "start_sha": BASE},
            "head_pipeline": {
                "id": 42,
                "project_id": 71,
                "sha": HEAD,
                "status": "running",
                "ref": "refs/merge-requests/509/head",
            },
        }
        self.approvals = {"approved": True, "approved_by": []}
        self.approval_state = {"rules": []}
        self.version = {
            "id": 100,
            "head_commit_sha": HEAD,
            "base_commit_sha": BASE,
            "start_commit_sha": BASE,
            "created_at": "2026-11-24T12:00:10Z",
        }
        self.reviewer_pages = [[]]
        self.discussion_pages = [[]]
        self.job_pages = [
            [
                {
                    "name": "Playwright E2E Sharded 1/2",
                    "id": 100,
                    "status": "running",
                    "allow_failure": False,
                }
            ]
        ]
        self.calls = []
        self.confirmation = None
        self.merge_commit = {"id": SYNTHETIC, "parent_ids": [BASE, HEAD]}

    def command(self, args):
        assert args[:4] == ["glab", "api", "--hostname", HOST], args
        endpoint = args[-1]
        self.calls.append(endpoint)
        if endpoint == MR:
            result = self.mr
            if self.confirmation and self.calls.count(MR) % 2 == 0:
                result = self.confirmation
            return json.dumps(result)
        if endpoint == "user":
            return json.dumps({"username": "watcher"})
        if endpoint == MR + "/approvals":
            return json.dumps(self.approvals)
        if endpoint == MR + "/approval_state":
            if self.approval_state is None:
                raise RuntimeError("Approval rule details unavailable")
            return json.dumps(self.approval_state)
        if endpoint == MR + "/versions?per_page=1":
            return json.dumps([self.version])
        if endpoint == f"projects/71/repository/commits/{SYNTHETIC}":
            return json.dumps(self.merge_commit)
        pages = {
            MR + "/reviewers?per_page=100": self.reviewer_pages,
            MR + "/discussions?per_page=100": self.discussion_pages,
            JOBS: self.job_pages,
        }
        assert args[4] == "--paginate", args
        return json_pages(*pages[endpoint])

    def snapshot(self, jobs=(), until_ready=True):
        with patch.object(watch, "command", side_effect=self.command):
            return watch.read_watch_snapshot(
                {
                    "provider": "gitlab",
                    "host": HOST,
                    "repo": PROJECT,
                    "number": NUMBER,
                    "jobs": jobs,
                    "actor": "watcher",
                    "until_ready": until_ready,
                }
            )

    def finish_pipeline(self, status):
        self.mr["head_pipeline"]["status"] = status
        self.mr["detailed_merge_status"] = (
            "mergeable" if status == "success" else "ci_must_pass"
        )
        self.job_pages[0][0]["status"] = status

    def approve(self, timestamp, user=9):
        self.approvals["approved_by"].append(
            {"user": {"id": user}, "approved_at": timestamp}
        )


class GitLabWatchTest(unittest.TestCase):
    def test_reopened_discussion_is_feedback_even_without_a_new_note(self):
        responses = GitLabResponses()
        note = {
            "id": 3,
            "author": {"username": "reviewer"},
            "body": "existing review",
            "resolvable": True,
            "resolved": True,
        }
        responses.discussion_pages = [[{"id": "thread-a", "notes": [note]}]]
        resolved = responses.snapshot()
        note["resolved"] = False
        reopened = responses.snapshot()

        event, _ = watch.detect(resolved, reopened, None)
        self.assertEqual(
            event, {"kind": "feedback", "records": ["discussion:thread-a"]}
        )
        self.assertEqual(watch.detect(reopened, reopened, None), (None, None))
        self.assertEqual(watch.detect(reopened, resolved, None), (None, None))

    def test_paginated_reviews_include_replies_and_edits_without_storing_bodies(self):
        responses = GitLabResponses()
        responses.discussion_pages = [
            [
                {
                    "id": "first",
                    "notes": [
                        {
                            "id": 1,
                            "author": {"username": "watcher"},
                            "body": "own reply",
                        },
                        {"id": 2, "system": True, "body": "added commits"},
                    ],
                }
            ],
            [
                {
                    "id": "second",
                    "notes": [
                        {
                            "id": 3,
                            "author": {"username": "reviewer"},
                            "body": "review comment",
                        },
                        {
                            "id": 4,
                            "author": {"username": "reviewer"},
                            "body": "review reply",
                        },
                    ],
                }
            ],
        ]
        initial = responses.snapshot()
        self.assertEqual(set(initial["feedback"]), {"note:3", "note:4", "review:state"})
        self.assertNotIn("review comment", json.dumps(initial))
        responses.discussion_pages[1][0]["notes"][0]["body"] = "edited"
        responses.reviewer_pages.append(
            [{"state": "requested_changes", "user": {"id": 9}}]
        )
        current = responses.snapshot()
        event, _ = watch.detect(initial, current, None)
        self.assertEqual(event["kind"], "feedback")
        self.assertEqual(event["records"], ["note:3", "review:state"])

    def test_failed_aggregate_is_delivered_even_when_selected_job_succeeded_and_feedback_arrived(
        self,
    ):
        responses = GitLabResponses()
        responses.job_pages.append(
            [
                {
                    "name": "PHPUnit",
                    "id": 101,
                    "status": "success",
                    "allow_failure": False,
                }
            ]
        )
        initial = responses.snapshot(["PHPUnit"])
        responses.finish_pipeline("failed")
        responses.discussion_pages = [
            [
                {
                    "notes": [
                        {
                            "id": 12,
                            "author": {"username": "reviewer"},
                            "body": "check Playwright",
                        }
                    ]
                }
            ]
        ]
        failed = responses.snapshot(["PHPUnit"])
        event, _ = watch.detect(initial, failed, None)
        self.assertEqual(event["kind"], "pipelines_completed")
        self.assertEqual(event["runs"]["42"]["conclusion"], "failure")
        self.assertEqual(event["records"], ["note:12"])
        self.assertFalse(watch.ready(failed))
        self.assertIsNone(watch.detect(failed, failed, None)[0])

    def test_pipeline_completion_does_not_depend_on_expected_jobs_being_present(self):
        responses = GitLabResponses()
        initial = responses.snapshot(["Missing job"])
        responses.finish_pipeline("success")
        responses.approve("2026-11-24T12:00:11Z")
        current = responses.snapshot(["Missing job"])
        self.assertEqual(
            watch.detect(initial, current, None)[0]["kind"], "pipelines_completed"
        )
        self.assertFalse(watch.ready(current))

    def test_allowed_failed_job_is_reported_as_warning_on_green_pipeline(self):
        responses = GitLabResponses()
        initial = responses.snapshot(["Playwright E2E Sharded 1/2"])
        responses.finish_pipeline("success")
        responses.approve("2026-11-24T12:00:11Z")
        responses.job_pages.append(
            [
                {
                    "id": 103,
                    "name": "Experimental checks",
                    "status": "failed",
                    "allow_failure": True,
                },
                {
                    "id": 104,
                    "name": "Optional success",
                    "status": "success",
                    "allow_failure": True,
                },
            ]
        )
        current = responses.snapshot(["Playwright E2E Sharded 1/2"])
        self.assertTrue(watch.ready(current))
        self.assertEqual(set(current["ci_warnings"]), {"job:71:103"})
        self.assertEqual(current["ci_warnings"]["job:71:103"]["pipeline_id"], "42")
        self.assertNotIn("Experimental checks", json.dumps(current))
        responses.mr["state"] = "merged"
        final = responses.snapshot()
        events, _ = self.daemon_events(
            initial, [current, current, current, final], until_ready=True
        )
        self.assertEqual(
            [event["kind"] for event, _, _ in events],
            ["pipelines_completed", "approved_and_green", "merged"],
        )
        self.assertEqual(set(events[0][0]["ci_warnings"]), {"job:71:103"})
        self.assertIn("job 103 (allowed failure)", events[0][2])
        self.assertNotIn("ci_warnings", events[1][0])

    def test_report_pipeline_warning_when_no_warning_job_is_listed(self):
        responses = GitLabResponses()
        responses.finish_pipeline("success")
        responses.mr["head_pipeline"]["detailed_status"] = {
            "group": "success-with-warnings"
        }
        current = responses.snapshot()
        self.assertEqual(set(current["ci_warnings"]), {"pipeline:71:42"})
        responses.mr["state"] = "closed"
        events, _ = self.daemon_events(
            current, [current, current, responses.snapshot()], until_ready=True
        )
        self.assertEqual(
            [event["kind"] for event, _, _ in events], ["ci_warnings", "closed"]
        )
        self.assertIn("pipeline 42 (passed with warnings)", events[0][2])

    def test_approval_needs_current_diff_and_no_outstanding_changes(self):
        responses = GitLabResponses()
        responses.finish_pipeline("success")
        self.assertFalse(watch.ready(responses.snapshot()))  # No actual approver.
        responses.approve("2026-11-24T12:00:09Z")
        self.assertFalse(watch.ready(responses.snapshot()))
        responses.approvals["approved_by"].clear()
        responses.approve(None)
        self.assertFalse(watch.ready(responses.snapshot()))
        responses.approvals["approved_by"].clear()
        responses.approve("2026-11-24T12:00:11Z")
        self.assertTrue(watch.ready(responses.snapshot()))
        responses.approve("2026-11-24T12:00:09Z", user=10)
        responses.approval_state["rules"] = [
            {"approvals_required": 1, "approved": True, "approved_by": [{"id": 10}]},
        ]
        self.assertFalse(watch.ready(responses.snapshot()))
        responses.approvals["approved_by"].pop()
        responses.version["head_commit_sha"] = NEXT
        self.assertFalse(watch.ready(responses.snapshot()))
        responses.version["head_commit_sha"] = HEAD
        responses.mr["detailed_merge_status"] = "approvals_syncing"
        self.assertFalse(watch.ready(responses.snapshot()))
        responses.mr["detailed_merge_status"] = "mergeable"
        responses.reviewer_pages = [
            [{"state": "requested_changes", "user": {"id": 12}}]
        ]
        self.assertFalse(watch.ready(responses.snapshot()))

    def test_old_optional_vote_does_not_block_current_votes_that_satisfy_the_rules(
        self,
    ):
        responses = GitLabResponses()
        responses.finish_pipeline("success")
        responses.approve("2026-11-24T12:00:11Z", user=9)
        responses.approve("2026-11-24T12:00:09Z", user=10)
        responses.approve("2026-11-24T12:00:12Z", user=11)
        first = {
            "approvals_required": 1,
            "approved": True,
            "approved_by": [{"id": 9}, {"id": 10}],
        }
        second = {
            "approvals_required": 1,
            "approved": True,
            "approved_by": [{"id": 11}],
        }
        optional = {
            "approvals_required": 0,
            "approved": True,
            "approved_by": [{"id": 10}],
        }
        responses.approval_state["rules"] = [first, second, optional]
        current = responses.snapshot()
        self.assertTrue(watch.ready(current))
        self.assertEqual(set(current["opinions"]), {"9", "11"})
        first["approvals_required"] = 2
        self.assertFalse(watch.ready(responses.snapshot()))

    def test_missing_approval_rule_details_do_not_hide_completed_pipeline(self):
        responses = GitLabResponses()
        initial = responses.snapshot()
        responses.finish_pipeline("success")
        responses.approve("2026-11-24T12:00:11Z", user=9)
        responses.approve("2026-11-24T12:00:09Z", user=10)
        responses.approval_state = None
        current = responses.snapshot()
        self.assertIn(MR + "/approval_state", responses.calls)
        self.assertFalse(watch.ready(current))
        self.assertEqual(
            watch.detect(initial, current, None)[0]["kind"], "pipelines_completed"
        )

    def test_head_change_ignores_old_pipeline_and_notifies_once(self):
        responses = GitLabResponses()
        responses.finish_pipeline("success")
        responses.approve("2026-11-24T12:00:11Z")
        previous = responses.snapshot()
        responses.mr["sha"] = NEXT
        current = responses.snapshot()
        self.assertEqual(current["runs"], {})
        self.assertFalse(watch.ready(current))
        event, _ = watch.detect(previous, current, None)
        self.assertEqual(event["kind"], "head_changed")
        self.assertIsNone(watch.detect(current, current, None)[0])

    def test_merged_result_pipeline_requires_current_source_head_as_parent(self):
        responses = GitLabResponses()
        responses.finish_pipeline("success")
        responses.approve("2026-11-24T12:00:11Z")
        responses.mr["head_pipeline"].update(
            sha=SYNTHETIC, ref="refs/merge-requests/509/merge"
        )
        self.assertTrue(watch.ready(responses.snapshot()))
        responses.merge_commit["parent_ids"] = [HEAD, NEXT]
        self.assertEqual(responses.snapshot()["runs"], {})

    def test_inconsistent_head_or_pipeline_status_is_retried_without_an_event(self):
        for field in ("sha", "pipeline"):
            with self.subTest(field=field):
                responses = GitLabResponses()
                responses.confirmation = deepcopy(responses.mr)
                if field == "sha":
                    responses.confirmation["sha"] = NEXT
                else:
                    responses.confirmation["head_pipeline"]["status"] = "success"
                with self.assertRaises(RuntimeError):
                    responses.snapshot()

    def test_daemon_delivers_failure_ready_and_final_outcome_once_under_original_deadline(
        self,
    ):
        for terminal in ("merged", "closed"):
            with (
                self.subTest(terminal=terminal),
                tempfile.TemporaryDirectory() as directory,
            ):
                responses = GitLabResponses()
                initial = responses.snapshot()
                responses.finish_pipeline("failed")
                failed = responses.snapshot()
                responses.job_pages[0][0].update(id=102, status="running")
                responses.mr["head_pipeline"]["status"] = "running"
                retry = responses.snapshot()
                responses.finish_pipeline("success")
                responses.approve("2026-11-24T12:00:11Z")
                good = responses.snapshot()
                responses.calls.clear()
                responses.mr["state"] = terminal
                responses.mr["sha"] = (
                    None  # Final state remains authoritative if the source is gone.
                )
                final = responses.snapshot()
                self.assertEqual(responses.calls, [MR])
                path = Path(directory) / "state.json"
                state = {
                    "provider": "gitlab",
                    "host": HOST,
                    "repo": PROJECT,
                    "number": NUMBER,
                    "thread": "owning-chat",
                    "actor": "watcher",
                    "jobs": [],
                    "workflows": [],
                    "until_ready": True,
                    "delivery": "daemon",
                    "deadline": 1000,
                    "interval": 60,
                    "state_path": str(path),
                    "snapshot": initial,
                }
                watch.atomic(path, state)
                snapshots = [failed, failed, retry, good, good, good, final]
                kinds = []

                def record_delivery(state, _message):
                    kinds.append(state["event"]["kind"])
                    return "matching turn completed"

                with (
                    patch.object(watch.time, "time", return_value=100),
                    patch.object(watch.time, "sleep"),
                    patch.object(watch.signal, "signal"),
                    patch.object(
                        watch, "read_watch_snapshot", side_effect=snapshots
                    ) as read,
                    patch(
                        "daemon_delivery.deliver", side_effect=record_delivery
                    ) as deliver,
                ):
                    watch.run(path)
                self.assertEqual(read.call_count, len(snapshots))
                self.assertEqual(
                    kinds,
                    [
                        "pipelines_completed",
                        "pipelines_completed",
                        "approved_and_green",
                        terminal,
                    ],
                )
                failure, *_, ending = [call.args[1] for call in deliver.call_args_list]
                self.assertIn("Pipeline 42: failed", failure)
                self.assertNotIn("Playwright", failure)
                self.assertIn(
                    f"https://{HOST}/{PROJECT}/-/merge_requests/{NUMBER}", ending
                )
                self.assertIn(
                    (
                        "MR merged"
                        if terminal == "merged"
                        else "MR closed without merging"
                    ),
                    ending,
                )
                self.assertNotIn("process-pr-feedback", ending)
                saved = json.loads(path.read_text())
                self.assertEqual((saved["status"], saved["deadline"]), (terminal, 1000))

    def daemon_events(self, initial, snapshots, **mode):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = {
                "provider": "gitlab",
                "host": HOST,
                "repo": PROJECT,
                "number": NUMBER,
                "thread": "owning-chat",
                "actor": "watcher",
                "delivery": "daemon",
                "deadline": 1000,
                "interval": 60,
                "snapshot": initial,
                "state_path": str(path),
                **mode,
            }
            watch.atomic(path, state)
            events = []

            def record_state(state, _message):
                events.append(
                    (deepcopy(state["event"]), deepcopy(state["snapshot"]), _message)
                )
                return "matching turn completed"

            with (
                patch.object(watch.time, "time", return_value=100),
                patch.object(watch.time, "sleep"),
                patch.object(watch.signal, "signal"),
                patch.object(watch, "read_watch_snapshot", side_effect=snapshots),
                patch("daemon_delivery.deliver", side_effect=record_state),
            ):
                watch.run(path)
            return events, json.loads(path.read_text())

    def test_daemon_canary_preserves_pending_pipeline_and_feedback(self):
        responses = GitLabResponses()
        initial = responses.snapshot()
        responses.finish_pipeline("failed")
        responses.discussion_pages = [
            [
                {
                    "notes": [
                        {
                            "id": 12,
                            "author": {"username": "reviewer"},
                            "body": "pipeline failure",
                        }
                    ]
                }
            ]
        ]
        changed = responses.snapshot()
        responses.mr["state"] = "closed"
        final = responses.snapshot()
        events, saved = self.daemon_events(
            initial, [changed, changed, final], until_ready=True, canary=True
        )
        self.assertEqual(
            [event["kind"] for event, _, _ in events],
            ["host_self_test", "pipelines_completed", "closed"],
        )
        self.assertEqual(events[0][1], initial)
        self.assertEqual(events[1][0]["records"], ["note:12"])
        self.assertEqual(saved["deadline"], 1000)

    def test_one_shot_daemon_stops_after_first_notification(self):
        responses = GitLabResponses()
        initial = responses.snapshot(until_ready=False)
        responses.finish_pipeline("failed")
        failed = responses.snapshot(until_ready=False)
        responses.mr["state"] = "closed"
        final = responses.snapshot(until_ready=False)
        events, saved = self.daemon_events(initial, [failed, final], until_ready=False)
        self.assertEqual(
            [event["kind"] for event, _, _ in events], ["pipelines_completed"]
        )
        self.assertEqual(saved["status"], "complete")
        self.assertIn("notification-only", events[0][2])
        self.assertNotIn("continue the already-authorized task", events[0][2])

    def test_cli_reuses_matching_watch_and_separates_provider_and_hosts(self):
        responses = GitLabResponses()
        responses.finish_pipeline("failed")
        snapshot = responses.snapshot()
        gitlab = ["--provider", "gitlab", "--repo", PROJECT, "--number", str(NUMBER)]
        github = ["--repo", "group/project", "--number", str(NUMBER)]
        with tempfile.TemporaryDirectory() as directory:

            def start(extra):
                with (
                    patch.object(
                        watch.sys,
                        "argv",
                        [
                            "watch.py",
                            "start",
                            "--thread",
                            "owning-chat",
                            "--delivery",
                            "queue",
                            *extra,
                        ],
                    ),
                    patch.object(watch.os, "environ", {"CODEX_HOME": directory}),
                    patch("builtins.print") as printed,
                ):
                    watch.main()
                    return json.loads(printed.call_args.args[0])

            def command(args):
                if args[0] == "codex":
                    return ""
                if args[:2] == ["glab", "api"]:
                    self.assertEqual(args[2], "--hostname")
                    self.assertIn(args[3], (HOST, "gitlab.other.example.com"))
                    self.assertEqual(args[4:], ["user"])
                    return '{"username":"watcher"}'
                raise AssertionError(args)

            with (
                patch.object(watch, "command", side_effect=command),
                patch.object(watch, "api", return_value={"login": "watcher"}),
                patch.object(watch, "read_watch_snapshot", return_value=snapshot),
                patch.object(watch.time, "time", return_value=100),
                patch.object(
                    watch.subprocess, "Popen", return_value=SimpleNamespace(pid=123)
                ) as spawn,
                patch.object(watch, "alive", return_value=True) as alive,
            ):
                first = start([*gitlab, "--host", HOST.upper()])
                same = start([*gitlab, "--host", HOST, "--repo", PROJECT.upper()])
                other = start([*gitlab, "--host", "gitlab.other.example.com"])
                hosted = start([*gitlab[:-4], *github, "--host", HOST])
                gh = start(github)
                self.assertEqual(spawn.call_count, 4)
                self.assertTrue(same["already_running"])
                self.assertEqual(first["runs"]["42"]["pipeline_status"], "failed")
                self.assertEqual(first["state_path"], same["state_path"])
                self.assertEqual(
                    len(
                        {
                            first["state_path"],
                            other["state_path"],
                            hosted["state_path"],
                            gh["state_path"],
                        }
                    ),
                    4,
                )
                state = json.loads(Path(first["state_path"]).read_text())
                self.assertEqual(state["deadline"], 86500)
                self.assertEqual(
                    (state["host"], state["repo"], state["number"]),
                    (HOST, PROJECT, NUMBER),
                )
                alive.return_value = False
                with self.assertRaises(RuntimeError):
                    start([*gitlab, "--host", HOST])
                self.assertEqual(
                    json.loads(Path(first["state_path"]).read_text())["deadline"], 86500
                )
                self.assertEqual(spawn.call_count, 4)

    def test_queue_resume_keeps_gitlab_scope_and_deadline_until_final_delivery(self):
        responses = GitLabResponses()
        initial = responses.snapshot()
        responses.mr["state"] = "merged"
        final = responses.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = {
                "provider": "gitlab",
                "host": HOST,
                "repo": PROJECT,
                "number": NUMBER,
                "thread": "owning-chat",
                "actor": "watcher",
                "workflows": [],
                "jobs": [],
                "until_ready": True,
                "delivery": "queue",
                "resume_supported": False,
                "deadline": 1000,
                "status": "queued",
                "state_path": str(path),
                "snapshot": initial,
            }
            watch.atomic(path, state)
            with (
                patch.object(
                    watch.sys, "argv", ["watch.py", "resume", "--state", str(path)]
                ),
                patch.object(watch, "alive", return_value=False),
                patch.object(watch, "read_watch_snapshot", return_value=final) as read,
                patch.object(watch.time, "time", return_value=100),
                patch.object(
                    watch.subprocess, "Popen", return_value=SimpleNamespace(pid=123)
                ),
                patch("builtins.print"),
            ):
                watch.main()
            saved = json.loads(path.read_text())
            self.assertEqual(read.call_args.args[0]["host"], HOST)
            self.assertEqual(saved["deadline"], state["deadline"])
            self.assertEqual(saved["snapshot"], initial)
            self.assertEqual(
                watch.detect(saved["snapshot"], final, None)[0]["kind"], "merged"
            )

    def test_slow_poll_cannot_deliver_after_the_original_deadline(self):
        responses = GitLabResponses()
        initial = responses.snapshot()
        responses.finish_pipeline("failed")
        failed = responses.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            state = {
                "provider": "gitlab",
                "state_path": str(path),
                "interval": 60,
                "deadline": 1000,
                "until_ready": True,
                "delivery": "daemon",
                "snapshot": initial,
            }
            watch.atomic(path, state)
            now = 100

            def slow_read(_state):
                nonlocal now
                now = 1001
                return failed

            with (
                patch.object(watch.time, "time", side_effect=lambda: now),
                patch.object(watch.time, "sleep"),
                patch.object(watch.signal, "signal"),
                patch.object(watch, "read_watch_snapshot", side_effect=slow_read),
                patch.object(
                    watch, "notify", return_value="unexpected delivery"
                ) as notify,
            ):
                watch.run(path)
            self.assertEqual(json.loads(path.read_text())["status"], "expired")
            notify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
