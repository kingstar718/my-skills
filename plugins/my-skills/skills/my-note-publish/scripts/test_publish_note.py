"""Offline API contract checks: python -m unittest discover -s scripts -p 'test_*.py'."""

import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT = Path(__file__).with_name("publish_note.py")


class PublishTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.body = self.root / "body.md"
        self.body.write_text("今天试一下随记。\n\n保留 Markdown 和中文。\n", encoding="utf-8")
        self.prepared = self.root / "prepared.json"
        self.remote = None
        self.puts = 0
        self.mode = "normal"
        case = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, body):
                data = body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                if self.headers.get("Authorization") != "Bearer test-secret":
                    return self.reply(401, "unauthorized")
                if case.mode == "redirect":
                    self.send_response(302)
                    self.send_header("Location", "/other")
                    self.end_headers()
                    return
                if case.remote is None:
                    return self.reply(404, "missing")
                return self.reply(200, "different" if case.mode == "mismatch" else case.remote)

            def do_PUT(self):
                case.puts += 1
                case.remote = self.rfile.read(int(self.headers["Content-Length"])).decode("utf-8")
                if case.mode == "uncertain":
                    return self.reply(500, "server error after saving")
                return self.reply(200, json.dumps({"ok": True, "deployTriggered": case.mode != "no-deploy"}))

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.env = {**os.environ, "PYTHONUTF8": "1", "BLOG_ADMIN_PASSWORD": "test-secret",
                    "BLOG_BASE_URL": f"http://127.0.0.1:{self.server.server_port}",
                    "BLOG_NOTE_CONFIG": str(self.root / "config.json")}

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.directory.cleanup()

    def call(self, *args, env=None):
        done = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], env=env or self.env,
                              capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertNotIn("test-secret", done.stdout + done.stderr)
        return done.returncode, json.loads(done.stdout)

    def prepare(self, *extra):
        code, result = self.call("prepare", "--file", self.body, "--out", self.prepared,
                                 "--id", "test-note", *extra)
        self.assertEqual(code, 0, result)
        return json.loads(self.prepared.read_text(encoding="utf-8"))

    def publish(self, *extra, **kwargs):
        return self.call("publish", "--prepared", self.prepared, *extra, **kwargs)

    def test_unicode_time_and_draft(self):
        record = self.prepare("--pub-datetime", "2026-10-13T14:00:00+08:00", "--draft")
        self.assertIn('pubDatetime: "2026-10-13T06:00:00.000Z"', record["markdown"])
        self.assertIn("draft: true\n", record["markdown"])
        self.assertTrue(record["markdown"].endswith(self.body.read_text(encoding="utf-8")))
        self.assertNotIn("title:", record["markdown"])

    def test_preview_needs_no_credentials_or_network(self):
        self.prepare()
        code, result = self.publish("--dry-run", env={"PYTHONUTF8": "1"})
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "preview")
        self.assertEqual(self.puts, 0)

    def test_save_verify_and_sequential_retry(self):
        record = self.prepare()
        code, result = self.publish()
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "saved_verified")
        self.assertTrue(result["deployTriggered"])
        self.assertEqual(self.remote, record["markdown"])
        code, result = self.publish()
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "already_saved")
        self.assertIsNone(result["deployTriggered"])
        self.assertEqual(self.puts, 1)

    def test_conflict_does_not_overwrite(self):
        self.prepare()
        self.remote = "old content"
        code, result = self.publish()
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "conflict")
        self.assertEqual(self.puts, 0)
        self.assertEqual(self.remote, "old content")

    def test_uncertain_save_retry_reads_remote(self):
        self.prepare()
        self.mode = "uncertain"
        code, result = self.publish()
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "save_uncertain")
        self.assertIsNone(result["saved"])
        code, result = self.publish()
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "already_saved")
        self.assertEqual(self.puts, 1)

    def test_deploy_failure_is_not_save_failure(self):
        self.prepare()
        self.mode = "no-deploy"
        code, result = self.publish()
        self.assertEqual(code, 0)
        self.assertTrue(result["saved"])
        self.assertTrue(result["verified"])
        self.assertFalse(result["deployTriggered"])

    def test_read_back_mismatch(self):
        self.prepare()
        self.mode = "mismatch"
        code, result = self.publish()
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "saved_unverified")
        self.assertTrue(result["saved"])
        self.assertFalse(result["verified"])

    def test_auth_and_redirect_fail_without_write(self):
        self.prepare()
        code, result = self.publish(env={**self.env, "BLOG_ADMIN_PASSWORD": "wrong"})
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "preflight_failed")
        self.mode = "redirect"
        code, result = self.publish()
        self.assertEqual(code, 1)
        self.assertIn("302", result["error"])
        self.assertEqual(self.puts, 0)

    def test_invalid_input_and_no_record_overwrite(self):
        code, result = self.call("prepare", "--file", self.body, "--out", self.prepared,
                                 "--pub-datetime", "2026-10-13T14:00:00")
        self.assertEqual(code, 1)
        self.assertFalse(self.prepared.exists())
        record = self.prepare()
        code, result = self.call("prepare", "--file", self.body, "--out", self.prepared)
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(self.prepared.read_text(encoding="utf-8")), record)
        record["markdown"] += "tampered"
        self.prepared.write_text(json.dumps(record), encoding="utf-8")
        code, result = self.publish()
        self.assertEqual(code, 1)
        self.assertEqual(self.puts, 0)

    def test_empty_oversized_and_unsafe_id(self):
        for body, note_id in [("  \n", "good"), ("中" * 333334, "good"), ("正文", "../escape")]:
            self.body.write_text(body, encoding="utf-8")
            code, result = self.call("prepare", "--file", self.body, "--out", self.prepared, "--id", note_id)
            self.assertEqual(code, 1, result)
            self.assertFalse(self.prepared.exists())

    def test_disallow_remote_http_before_network(self):
        self.prepare()
        code, result = self.publish(env={**self.env, "BLOG_BASE_URL": "http://example.com"})
        self.assertEqual(code, 1)
        self.assertEqual(self.puts, 0)

    def test_missing_config_returns_setup_hint(self):
        self.prepare()
        env = {**self.env, "BLOG_BASE_URL": "", "BLOG_ADMIN_PASSWORD": ""}
        code, result = self.publish(env=env)
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "missing_config")
        self.assertEqual(result["missing"], ["blog_domain", "blog_password"])
        self.assertIn("setup", result["nextCommand"])
        self.assertEqual(self.puts, 0)

    def test_saved_configuration_and_environment_override(self):
        from unittest.mock import patch
        from note_config import read_config, save_config
        self.prepare()
        with patch.dict(os.environ, self.env):
            status = save_config(self.env["BLOG_BASE_URL"], "test-secret")
            self.assertEqual(status["status"], "configured")
            self.assertEqual(read_config()["password"], "test-secret")
            raw = Path(self.env["BLOG_NOTE_CONFIG"]).read_text(encoding="utf-8")
            if os.name == "nt":
                self.assertNotIn("test-secret", raw)
                self.assertEqual(status["protection"], "windows-dpapi")
            else:
                self.assertEqual(Path(self.env["BLOG_NOTE_CONFIG"]).stat().st_mode & 0o777, 0o600)
        code, result = self.publish(env={**self.env, "BLOG_BASE_URL": "", "BLOG_ADMIN_PASSWORD": ""})
        self.assertEqual(code, 0, result)
        self.assertEqual(result["status"], "saved_verified")
        code, result = self.publish(env={**self.env, "BLOG_ADMIN_PASSWORD": "wrong"})
        self.assertEqual(code, 1)
        self.assertEqual(result["status"], "preflight_failed")

    def test_cancelled_setup_does_not_write_credentials(self):
        from unittest.mock import patch
        from note_config import ConfigError, setup
        with patch.dict(os.environ, self.env), patch("note_config.gui_credentials", side_effect=ConfigError("Setup cancelled")):
            with self.assertRaises(ConfigError):
                setup(gui=True)
        self.assertFalse(Path(self.env["BLOG_NOTE_CONFIG"]).exists())

    def test_domain_without_scheme_defaults_to_https(self):
        from note_config import normalize_origin
        self.assertEqual(normalize_origin(" blog.example.com/ "), "https://blog.example.com")

    @unittest.skipUnless(os.name == "nt", "Windows GUI syntax")
    def test_windows_dialog_script_parses_without_opening_window(self):
        from note_config import gui_credentials
        script = next(value for value in gui_credentials.__code__.co_consts
                      if isinstance(value, str) and "Add-Type -AssemblyName" in value)
        parser = "$e=$null; $t=$null; $s=[Console]::In.ReadToEnd(); [void][System.Management.Automation.Language.Parser]::ParseInput($s,[ref]$t,[ref]$e); if ($e.Count) { exit 1 }"
        done = subprocess.run(["powershell.exe", "-NoProfile", "-Command", parser], input=script,
                              capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(done.returncode, 0)


if __name__ == "__main__":
    unittest.main()
