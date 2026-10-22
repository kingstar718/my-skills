import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fail_log
import snapshot_env
import cc_hooks
import zcode_hooks


class FailureLogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"ENV_TOOL_LOG_DIR": self.temp.name})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def add(self, sig="spawn EPERM", **kwargs):
        return fail_log.add_entry(entry={"cmd": "vitest run", "sig": sig, **kwargs})

    def test_default_path_is_harness_neutral(self):
        expected = Path.home() / ".my-skills" / "env-tool-log"
        self.assertEqual(Path(fail_log.DEFAULT_DATA_DIR), expected)

    def test_explicit_directory_wins_without_legacy_warning(self):
        legacy = Path(self.temp.name) / "legacy"
        legacy.mkdir()
        (legacy / "failures.jsonl").write_text("old data", encoding="utf-8")
        stderr = io.StringIO()
        with patch.object(fail_log, "LEGACY_DATA_DIR", str(legacy)):
            with contextlib.redirect_stderr(stderr):
                self.assertEqual(fail_log.data_dir(), self.temp.name)
        self.assertEqual(stderr.getvalue(), "")

    def test_legacy_notice_keeps_data_in_place_and_stdout_clean(self):
        legacy = Path(self.temp.name) / "legacy"
        target = Path(self.temp.name) / "shared"
        legacy.mkdir()
        old = legacy / "failures.jsonl"
        old.write_text("old data", encoding="utf-8")
        stdout, stderr = io.StringIO(), io.StringIO()
        with patch.dict(os.environ, {"ENV_TOOL_LOG_DIR": ""}):
            with patch.object(fail_log, "DEFAULT_DATA_DIR", str(target)):
                with patch.object(fail_log, "LEGACY_DATA_DIR", str(legacy)):
                    with patch.object(fail_log, "_legacy_notice_shown", False):
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            self.assertEqual(fail_log.data_dir(), str(target))
                            fail_log.data_dir()
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue().count(str(legacy)), 1)
        self.assertIn("ENV_TOOL_LOG_DIR", stderr.getvalue())
        self.assertEqual(old.read_text(encoding="utf-8"), "old data")
        self.assertFalse((target / "failures.jsonl").exists())

    def test_snapshot_and_hooks_share_directory_resolver(self):
        for client in [snapshot_env, cc_hooks, zcode_hooks]:
            self.assertIs(client.fail_log, fail_log)
            self.assertEqual(client.fail_log.data_dir(), self.temp.name)

    def test_find_sig_returns_latest_record(self):
        first = self.add()["added"]
        fail_log.mark_fixed(first["sig"], "Use permitted process execution")
        self.add(cause="recurrence")
        self.assertEqual(fail_log.find_sig(first["sig"])["status"], "OPEN")

    def test_same_error_updates_one_record_across_recurrences(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "old fix")
        with patch.object(fail_log, "now", return_value="2026-10-22 18:00:00"):
            self.assertIn("duplicate", self.add(sig="SPAWN EPERM", cause="recurrence"))
        rows = fail_log.read_entries()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["count"], 2)
        self.assertEqual(rows[0]["last_seen"], "2026-10-22 18:00:00")
        self.assertEqual(rows[0]["status"], "OPEN")
        self.assertEqual(rows[0]["verified_fix"], "old fix")
        self.add()
        self.assertEqual(fail_log.read_entries()[0]["count"], 3)

    def test_legacy_duplicates_are_coalesced_only_for_matching_signature(self):
        self.add()
        fail_log.append_entry({"cmd": "vitest run", "sig": "spawn EPERM", "status": "FIXED", "fix": "known fix"})
        self.add(sig="unrelated")
        self.add(sig="SPAWN EPERM")
        rows = fail_log.read_entries()
        matches = [r for r in rows if r["sig"].lower() == "spawn eperm"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["count"], 3)
        self.assertEqual(len(rows), 2)

    def test_mark_fixed_updates_current_rule_without_counting_as_failure(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "old fix")
        self.add()
        self.assertEqual(fail_log.mark_fixed("spawn EPERM", "new fix"), 1)
        row = fail_log.read_entries()[0]
        self.assertEqual(row["verified_fix"], "new fix")
        self.assertEqual(row["count"], 2)
        self.assertEqual(fail_log.mark_fixed("spawn EPERM"), 0)

    def test_archived_error_is_reused_and_lesson_survives_archive(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "known fix")
        fail_log.prune(older_days=-1)
        self.assertEqual(fail_log.read_entries(), [])
        self.assertIn("known fix", fail_log.lessons()["snippet"])
        self.add()
        self.assertEqual(len(fail_log.read_entries()), 1)
        self.assertEqual(fail_log.read_entries()[0]["count"], 2)
        self.assertEqual(fail_log.read_entries(fail_log.archive_path()), [])

    def test_query_default_keeps_open_and_all_searches_fix(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "Use permitted process execution")
        self.add(sig="path missing")
        self.assertEqual([r["sig"] for r in fail_log.query()], ["path missing"])
        self.assertEqual(fail_log.query("permitted"), [])
        matches = fail_log.query("permitted", include_fixed=True)
        self.assertEqual([r["sig"] for r in matches], ["spawn EPERM"])

    def test_cli_all_retains_json_interface(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "Use permitted process execution")
        output = io.StringIO()
        with patch("sys.argv", ["fail_log.py", "query", "permitted", "--all", "--json"]):
            with contextlib.redirect_stdout(output):
                fail_log.main()
        self.assertEqual(json.loads(output.getvalue())[0]["status"], "FIXED")

    def test_lessons_use_verified_fix_and_latest_signature(self):
        self.add(cause="sandbox denies child process")
        fail_log.mark_fixed("spawn EPERM", "old approach")
        self.add(cause="sandbox denies child process")
        fail_log.mark_fixed("spawn EPERM", "Use permitted process execution")
        self.add(sig="still open", fix="unverified proposal")
        fail_log.append_entry({"cmd": "rg", "sig": "no fix", "status": "FIXED", "cause": "known"})
        snippet = fail_log.lessons()["snippet"]
        self.assertIn("sandbox denies child process", snippet)
        self.assertIn("Use permitted process execution", snippet)
        self.assertNotIn("old approach", snippet)
        self.assertNotIn("unverified proposal", snippet)
        self.assertNotIn("no fix", snippet)
        self.assertEqual(snippet.count("spawn EPERM"), 1)

    def test_recurrence_retains_verified_lesson_without_promoting_proposal(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "verified fix")
        self.add(fix="unverified proposal")
        snippet = fail_log.lessons()["snippet"]
        self.assertIn("verified fix", snippet)
        self.assertNotIn("unverified proposal", snippet)

    def test_builtin_tools_are_indexed_and_old_lessons_are_not_truncated(self):
        for i in range(10):
            fail_log.add_entry(entry={"cmd": "apply_patch", "tool": "apply_patch", "sig": f"patch-context-{i}"})
            fail_log.mark_fixed(f"patch-context-{i}", f"anchor-{i}")
        snippet = fail_log.lessons()["snippet"]
        self.assertIn("apply_patch", snippet)
        self.assertEqual(snippet.count("触发条件"), 10)

    def test_add_and_close_keep_index_current_automatically(self):
        self.add()
        fail_log.mark_fixed("spawn EPERM", "verified method")
        path = Path(self.temp.name) / "lessons.md"
        self.assertIn("verified method", path.read_text(encoding="utf-8"))
        self.add(fix="candidate method")
        pending = path.read_text(encoding="utf-8")
        self.assertIn("verified method", pending)
        self.assertNotIn("candidate method", pending)
        fail_log.mark_fixed("spawn EPERM", "replacement method")
        current = path.read_text(encoding="utf-8")
        self.assertIn("replacement method", current)
        self.assertNotIn("verified method", current)
        self.assertEqual(current.count("触发条件"), 1)

    def test_apply_lessons_is_idempotent_and_preserves_manual_text(self):
        self.add(cause="sandbox denies child process")
        fail_log.mark_fixed("spawn EPERM", "Use permitted process execution")
        path = Path(self.temp.name) / "lessons.md"
        path.write_text("# Manual guidance\n\nKeep this text.\n", encoding="utf-8")
        first = fail_log.lessons(apply=True)
        first_text = path.read_text(encoding="utf-8")
        self.assertEqual(first["applied"], str(path))
        fail_log.lessons(apply=True)
        self.assertEqual(path.read_text(encoding="utf-8"), first_text)
        self.assertIn("Keep this text.", first_text)
        self.add(sig="other failure")
        fail_log.mark_fixed("other failure", "another fix")
        fail_log.lessons(apply=True)
        updated = path.read_text(encoding="utf-8")
        self.assertIn("another fix", updated)
        self.assertEqual(updated.count("Use permitted process execution"), 1)
        self.assertIn("Keep this text.", updated)


if __name__ == "__main__":
    unittest.main()
