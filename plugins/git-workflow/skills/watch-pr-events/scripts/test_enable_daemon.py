"""Migration contracts: never stop a process that may already be delivering."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import enable_daemon as m
from state_io import delivery_guard


class MigrationTest(unittest.TestCase):
    def state(self, path):
        state = dict(
            repo="owner/repo",
            number=2,
            thread="abc",
            until_ready=True,
            deadline=99999999999,
            snapshot={"head": "a"},
            status="watching",
            handoff_protocol=1,
            pid=123,
            state_path=str(path),
        )
        m.watch.atomic(path, state)
        return state

    def daemon(self):
        return {"thread": {"id": "abc", "path": "rollout"}}

    def test_cli_socket_uses_codex_home_unless_explicitly_overridden(self):
        for extra, expected in (
            ([], "/custom/codex/app-server-control/app-server-control.sock"),
            (["--daemon-socket", "/explicit.sock"], "/explicit.sock"),
        ):
            with (
                patch.dict(m.os.environ, CODEX_HOME="/custom/codex"),
                patch.object(
                    m.os.sys,
                    "argv",
                    ["enable_daemon.py", "--state", "/tmp/state.json", *extra],
                ),
                patch.object(m, "prepare") as prepare,
                patch.object(m.os, "execv"),
            ):
                m.main()
            self.assertEqual(prepare.call_args.args[1], expected)

    def test_delivery_started_during_capability_check_is_not_killed_or_overwritten(
        self,
    ):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            state = self.state(path)

            def capability(*args):
                state.update(status="delivery_pending", event={"kind": "feedback"})
                m.watch.atomic(path, state)
                return self.daemon()

            with (
                patch.object(m, "RPC") as rpc,
                patch.object(m.os, "kill") as kill,
                patch.object(m.watch, "alive", return_value=True),
            ):
                rpc.return_value.call.side_effect = capability
                with self.assertRaises(RuntimeError):
                    m.prepare(path, "local", True)
            kill.assert_not_called()
            self.assertEqual(json.loads(path.read_text()), state)

    def test_delivery_lock_prevents_migration_even_before_state_transition(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            state = self.state(path)
            with (
                delivery_guard(path),
                patch.object(m, "RPC") as rpc,
                patch.object(m.os, "kill") as kill,
            ):
                rpc.return_value.call.return_value = self.daemon()
                with self.assertRaisesRegex(RuntimeError, "Delivery is in progress"):
                    m.prepare(path, "local", True)
            kill.assert_not_called()
            self.assertEqual(json.loads(path.read_text()), state)

    def test_verified_waiter_stops_before_migration_preserving_cursor_and_deadline(
        self,
    ):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            state = self.state(path)

            def stopped(*args):
                state["status"] = "cancelled"
                m.watch.atomic(path, state)

            with (
                patch.object(m, "RPC") as rpc,
                patch.object(m.os, "kill", side_effect=stopped) as kill,
                patch.object(m.watch, "alive", side_effect=[True, False, False]),
            ):
                rpc.return_value.call.return_value = self.daemon()
                m.prepare(path, "local", True)
            kill.assert_called_once_with(123, m.signal.SIGTERM)
            migrated = json.loads(path.read_text())
            self.assertEqual(migrated["deadline"], state["deadline"])
            self.assertEqual(migrated["snapshot"], state["snapshot"])
            self.assertEqual(migrated["status"], "queued")
            self.assertTrue(migrated["canary"])

    def test_legacy_live_waiter_requires_manual_stop_and_inspection(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "state.json"
            state = self.state(path)
            state.pop("handoff_protocol")
            m.watch.atomic(path, state)
            with (
                patch.object(m, "RPC") as rpc,
                patch.object(m.os, "kill") as kill,
                patch.object(m.watch, "alive", return_value=True),
            ):
                rpc.return_value.call.return_value = self.daemon()
                with self.assertRaisesRegex(
                    RuntimeError, "lacks delivery synchronization"
                ):
                    m.prepare(path, "local")
            kill.assert_not_called()


if __name__ == "__main__":
    unittest.main()
