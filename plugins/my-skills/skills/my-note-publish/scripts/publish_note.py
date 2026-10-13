#!/usr/bin/env python3
"""Prepare and publish title-free notes through the blog content API."""

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from note_config import ConfigError, resolve_config, setup

MAX_BYTES = 1_000_000


class NoteError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def emit(result):
    print(json.dumps(result, ensure_ascii=False))


def valid_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,119}", value):
        raise NoteError("ID must contain 1–120 lowercase letters, digits or hyphens")
    return value


def utc_time(value=None):
    try:
        date = datetime.fromisoformat(value.replace("Z", "+00:00")) if value else datetime.now(timezone.utc)
        if date.tzinfo is None or date.utcoffset() is None:
            raise ValueError()
        return date.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    except (ValueError, OverflowError):
        raise NoteError("Publication time must be ISO8601 with Z or an explicit offset") from None


def check_markdown(markdown):
    if not isinstance(markdown, str) or len(markdown.encode("utf-8")) > MAX_BYTES:
        raise NoteError("Markdown must be UTF-8 text of at most 1,000,000 bytes")


def prepare(args):
    body = Path(args.file).read_text(encoding="utf-8-sig")
    if not body.strip():
        raise NoteError("Note body is empty")
    if body.lstrip().startswith("---\n") or body.lstrip().startswith("---\r\n"):
        raise NoteError("Supply the body only, without frontmatter")
    timestamp = utc_time(args.pub_datetime)
    note_id = valid_id(args.id or f"{timestamp[:10]}-{uuid.uuid4().hex}")
    markdown = f'---\npubDatetime: "{timestamp}"\n' + ("draft: true\n" if args.draft else "") + f"---\n\n{body}"
    check_markdown(markdown)
    record = {"version": 1, "id": note_id, "markdown": markdown,
              "sha256": hashlib.sha256(markdown.encode("utf-8")).hexdigest()}
    with Path(args.out).open("x", encoding="utf-8") as target:
        json.dump(record, target, ensure_ascii=False, indent=2)
        target.write("\n")
    emit({"status": "prepared", "key": f"notes/{note_id}.md", "preparedFile": str(Path(args.out).resolve())})


def load_record(path):
    record = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("version") != 1:
        raise NoteError("Unsupported prepared record")
    note_id = valid_id(record.get("id"))
    markdown = record.get("markdown")
    check_markdown(markdown)
    if hashlib.sha256(markdown.encode("utf-8")).hexdigest() != record.get("sha256"):
        raise NoteError("Prepared record was modified; prepare a new record")
    # Restrict metadata even if a record was manually assembled with a matching hash.
    match = re.fullmatch(r'---\npubDatetime: "([^"\n]+)"\n(?:draft: true\n)?---\n\n([\s\S]+)', markdown)
    if not match or not match[2].strip() or utc_time(match[1]) != match[1]:
        raise NoteError("Invalid prepared note Markdown")
    return note_id, markdown


def endpoint(note_id, base):
    return f"{base}/api/content/notes/{note_id}.md"


def request(opener, url, password, method, timeout, body=None):
    req = Request(url, data=body, method=method, headers={
        "User-Agent": "mars-blog-note-publisher/1.0",
        "Authorization": f"Bearer {password}",
        "Content-Type": "text/markdown; charset=utf-8",
        "Cache-Control": "no-cache",
    })
    try:
        with opener.open(req, timeout=timeout) as response:
            data = response.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise NoteError(f"{method} response exceeds size limit")
            return data.decode("utf-8")
    except HTTPError as error:
        if method == "GET" and error.code == 404:
            return None
        raise NoteError(f"{method} failed with HTTP {error.code}") from None
    except (URLError, TimeoutError, OSError):
        raise NoteError(f"{method} failed: connection error or timeout") from None


def publish(args):
    note_id, markdown = load_record(args.prepared)
    result = {"key": f"notes/{note_id}.md", "saved": False, "verified": False, "deployTriggered": None}
    if args.dry_run:
        emit({**result, "status": "preview", "markdown": markdown})
        return 0
    base, password, missing = resolve_config()
    if missing:
        emit({**result, "status": "missing_config", "missing": missing,
              "nextCommand": "setup --gui" if os.name == "nt" else "setup"})
        return 1
    url = endpoint(note_id, base)
    result["apiUrl"] = url
    opener = build_opener(NoRedirect())
    phase = "preflight_failed"
    try:
        existing = request(opener, url, password, "GET", args.timeout)
        if existing is not None:
            if existing != markdown:
                emit({**result, "status": "conflict", "error": "Remote note differs; refusing to overwrite"})
                return 1
            emit({**result, "status": "already_saved", "saved": True, "verified": True})
            return 0
        phase = "save_uncertain"
        result["saved"] = None
        raw = request(opener, url, password, "PUT", args.timeout, markdown.encode("utf-8"))
        response = json.loads(raw)
        if not isinstance(response, dict) or response.get("ok") is not True:
            raise NoteError("Unexpected PUT response; read remote note before retrying")
        result["saved"] = True
        phase = "saved_unverified"
        triggered = response.get("deployTriggered")
        result["deployTriggered"] = triggered if isinstance(triggered, bool) else None
        if request(opener, url, password, "GET", args.timeout) != markdown:
            raise NoteError("Read-back does not match prepared note")
        emit({**result, "status": "saved_verified", "verified": True})
        return 0
    except (NoteError, ValueError, UnicodeError) as error:
        message = str(error) if isinstance(error, NoteError) else "Invalid UTF-8 or JSON response"
        emit({**result, "status": phase, "error": message})
        return 1


def timeout_seconds(value):
    number = int(value)
    if not 1 <= number <= 120:
        raise argparse.ArgumentTypeError("timeout must be 1–120 seconds")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    configure = commands.add_parser("setup", help="Prompt for blog domain and password, then save local configuration")
    configure.add_argument("--gui", action="store_true", help="Use a Windows dialog instead of terminal input")
    prep = commands.add_parser("prepare", help="Wrap a UTF-8 body and persist a reusable publish record")
    prep.add_argument("--file", required=True)
    prep.add_argument("--out", required=True)
    prep.add_argument("--id")
    prep.add_argument("--pub-datetime")
    prep.add_argument("--draft", action="store_true")
    pub = commands.add_parser("publish", help="Publish a prepared record, or preview without network access")
    pub.add_argument("--prepared", required=True)
    pub.add_argument("--dry-run", action="store_true")
    pub.add_argument("--timeout", type=timeout_seconds, default=30)
    args = parser.parse_args()
    try:
        if args.command == "setup":
            emit(setup(gui=args.gui))
            return 0
        if args.command == "prepare":
            prepare(args)
            return 0
        return publish(args)
    except (NoteError, ConfigError, OSError, ValueError, UnicodeError, EOFError) as error:
        message = str(error) if isinstance(error, (NoteError, ConfigError)) else "Cannot read/write input, or invalid record/URL"
        emit({"status": "failed", "error": message})
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
