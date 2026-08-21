#!/usr/bin/env python3
"""env-tool-log: persistent tool-call failure log (JSONL, cross-platform)."""
import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timedelta

DATA_DIR_ENV = "ENV_TOOL_LOG_DIR"
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".codex", "skills-data", "env-tool-log")
FAILURES_FILE = "failures.jsonl"
ARCHIVE_FILE = "failures-archive.jsonl"
LESSONS_FILE = "lessons.md"

STATUS_OPEN = "OPEN"
STATUS_FIXED = "FIXED"
CATEGORIES = ["env", "syntax", "args", "path", "network", "api", "auth", "other"]


def data_dir() -> str:
    d = os.environ.get(DATA_DIR_ENV) or DEFAULT_DATA_DIR
    os.makedirs(d, exist_ok=True)
    return d


def failures_path() -> str:
    return os.path.join(data_dir(), FAILURES_FILE)


def archive_path() -> str:
    return os.path.join(data_dir(), ARCHIVE_FILE)


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_entries(path=None) -> list:
    path = path or failures_path()
    entries = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def write_entries(entries: list) -> None:
    with open(failures_path(), "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def append_entry(entry: dict) -> dict:
    entry = dict(entry)
    entry.setdefault("ts", now())
    entry.setdefault("status", STATUS_OPEN)
    entry.setdefault("category", "other")
    entry.setdefault("cause", "")
    entry.setdefault("fix", "")
    entry.setdefault("from", "codex")
    with open(failures_path(), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def find_sig(sig: str, entries=None) -> dict:
    sig = (sig or "").strip().lower()
    if not sig:
        return None
    entries = entries if entries is not None else read_entries()
    for e in entries:
        if (e.get("sig") or "").strip().lower() == sig:
            return e
    return None


def add_entry(args=None, entry: dict = None) -> dict:
    if entry is None:
        entry = {}
    cmd = entry.get("cmd") or (getattr(args, "cmd", None) if args else None)
    sig = entry.get("sig") or (getattr(args, "sig", None) if args else None)
    if not cmd or not sig:
        return {"error": "cmd and sig are required"}
    existing = find_sig(sig)
    if existing and existing.get("status") == STATUS_OPEN:
        return {"duplicate": existing}
    category = entry.get("category") or (getattr(args, "category", None) if args else None) or "other"
    if category not in CATEGORIES:
        category = "other"
    e = append_entry({
        "cmd": str(cmd),
        "sig": str(sig),
        "category": category,
        "cause": entry.get("cause") or (getattr(args, "cause", "") if args else "") or "",
        "fix": entry.get("fix") or (getattr(args, "fix", "") if args else "") or "",
        "from": entry.get("from") or (getattr(args, "from_", None) if args else None) or "codex",
    })
    return {"added": e}


def mark_fixed(sig: str, fix: str = "") -> int:
    entries = read_entries()
    updated = 0
    sig = (sig or "").strip().lower()
    for e in entries:
        if (e.get("sig") or "").strip().lower() == sig:
            e["status"] = STATUS_FIXED
            e["ts_fixed"] = now()
            if fix:
                e["fix"] = fix
            updated += 1
    if updated:
        write_entries(entries)
    return updated


def query(pattern: str = "", include_fixed: bool = False, limit: int = 20) -> list:
    entries = read_entries()
    if pattern:
        p = pattern.strip().lower()
        entries = [
            e for e in entries
            if p in (e.get("cmd") or "").lower()
            or p in (e.get("sig") or "").lower()
            or p in (e.get("cause") or "").lower()
        ]
    if not include_fixed:
        entries = [e for e in entries if e.get("status") == STATUS_OPEN]
    if limit:
        entries = entries[-limit:]
    return entries


def prune(older_days: int = 90, max_entries: int = 500) -> dict:
    entries = read_entries()
    archived = []
    cutoff = datetime.now() - timedelta(days=older_days)
    keep = []
    for e in entries:
        if e.get("status") == STATUS_FIXED:
            try:
                t = datetime.strptime(e.get("ts_fixed") or e.get("ts"), "%Y-%m-%d %H:%M:%S")
            except ValueError:
                t = datetime.now()
            if t < cutoff:
                archived.append(e)
                continue
        keep.append(e)
    if len(keep) > max_entries:
        fixed = sorted(
            [e for e in keep if e.get("status") == STATUS_FIXED],
            key=lambda e: e.get("ts", ""),
        )
        overflow = fixed[: len(keep) - max_entries]
        # 按 id() 而非内容过滤：内容完全相同的记录只删溢出部分，不连带误删
        overflow_ids = {id(e) for e in overflow}
        keep = [e for e in keep if id(e) not in overflow_ids]
        archived.extend(overflow)
    if archived:
        with open(archive_path(), "a", encoding="utf-8") as f:
            for e in archived:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        write_entries(keep)
    return {"archived": len(archived), "remaining": len(keep)}


def lessons(apply: bool = False, limit: int = 8) -> dict:
    entries = read_entries()
    fixed = [e for e in entries if e.get("status") == STATUS_FIXED and (e.get("cause") or e.get("fix"))]
    cat_counter = Counter(e.get("category", "other") for e in fixed)
    words = []
    for e in fixed:
        text = " ".join([e.get("cause", ""), e.get("fix", "")])
        for token in text.replace("，", " ").replace("。", " ").replace(",", " ").replace("；", " ").split():
            if len(token) >= 2:
                words.append(token.lower())
    kw = Counter(words).most_common(limit)
    lines = [f"## 教训（{now()} 自动提炼）", ""]
    if cat_counter:
        lines.append("按类别统计：")
        for cat, n in cat_counter.most_common():
            lines.append(f"- {cat}: {n} 条")
        lines.append("")
    lines.append("高频关键词（来自已修复记录）：")
    for w, n in kw:
        lines.append(f"- `{w}` x{n}")
    snippet = "\n".join(lines) + "\n"
    if apply:
        lp = os.path.join(data_dir(), LESSONS_FILE)
        with open(lp, "a", encoding="utf-8") as f:
            f.write(snippet)
        return {"applied": lp, "snippet": snippet}
    return {"snippet": snippet}


def fmt(e: dict) -> str:
    return "[{ts}] [{status}] [{category}] cmd: {cmd} | sig: {sig} | cause: {cause} | fix: {fix}".format(
        ts=e.get("ts", ""),
        status=e.get("status", ""),
        category=e.get("category", ""),
        cmd=e.get("cmd", ""),
        sig=e.get("sig", ""),
        cause=e.get("cause", ""),
        fix=e.get("fix", ""),
    )


def cmd_add(args) -> None:
    if getattr(args, "stdin", False):
        try:
            entry = json.load(sys.stdin)
        except json.JSONDecodeError:
            print(json.dumps({"error": "invalid JSON on stdin"}, ensure_ascii=False))
            return
        res = add_entry(entry=entry)
    else:
        res = add_entry(args=args)
    print(json.dumps(res, ensure_ascii=False))


def cmd_query(args) -> None:
    entries = query(args.pattern, include_fixed=args.all, limit=args.limit)
    if args.json:
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return
    if not entries:
        print("(no matching entries)")
        return
    for e in entries:
        print(fmt(e))


def cmd_mark_fixed(args) -> None:
    n = mark_fixed(args.sig, args.fix)
    print(json.dumps({"updated": n}, ensure_ascii=False))


def cmd_prune(args) -> None:
    print(json.dumps(prune(args.older_days, args.max), ensure_ascii=False))


def cmd_lessons(args) -> None:
    print(json.dumps(lessons(apply=args.apply), ensure_ascii=False))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="fail_log.py", description="env-tool-log failure log")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="record a failure")
    p_add.add_argument("--cmd")
    p_add.add_argument("--sig")
    p_add.add_argument("--cause", default="")
    p_add.add_argument("--fix", default="")
    p_add.add_argument("--category", default="other", choices=CATEGORIES)
    p_add.add_argument("--from", dest="from_", default="codex")
    p_add.add_argument("--stdin", action="store_true", help="read JSON entry from stdin")
    p_add.set_defaults(func=cmd_add)

    p_q = sub.add_parser("query", help="search failure log")
    p_q.add_argument("pattern", nargs="?", default="")
    p_q.add_argument("--all", action="store_true", help="include FIXED entries")
    p_q.add_argument("--limit", type=int, default=20)
    p_q.add_argument("--json", action="store_true")
    p_q.set_defaults(func=cmd_query)

    p_m = sub.add_parser("mark-fixed", help="mark entries FIXED by sig")
    p_m.add_argument("--sig", required=True)
    p_m.add_argument("--fix", default="")
    p_m.set_defaults(func=cmd_mark_fixed)

    p_p = sub.add_parser("prune", help="archive old FIXED entries")
    p_p.add_argument("--older-days", type=int, default=90)
    p_p.add_argument("--max", type=int, default=500)
    p_p.set_defaults(func=cmd_prune)

    p_l = sub.add_parser("lessons", help="distill lessons from FIXED entries")
    p_l.add_argument("--apply", action="store_true")
    p_l.set_defaults(func=cmd_lessons)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
