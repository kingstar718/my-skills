#!/usr/bin/env python3
"""env-tool-log: persistent tool-call failure log (JSONL, cross-platform)."""
import argparse
import json
import os
import sys
from datetime import datetime, timedelta

DATA_DIR_ENV = "ENV_TOOL_LOG_DIR"
DEFAULT_DATA_DIR = os.path.join(os.path.expanduser("~"), ".my-skills", "env-tool-log")
LEGACY_DATA_DIR = os.path.join(os.path.expanduser("~"), ".codex", "skills-data", "env-tool-log")
_legacy_notice_shown = False
FAILURES_FILE = "failures.jsonl"
ARCHIVE_FILE = "failures-archive.jsonl"
LESSONS_FILE = "lessons.md"

STATUS_OPEN = "OPEN"
STATUS_FIXED = "FIXED"
CATEGORIES = ["env", "syntax", "args", "path", "network", "api", "auth", "other"]


def data_dir() -> str:
    global _legacy_notice_shown
    override = os.environ.get(DATA_DIR_ENV)
    d = override or DEFAULT_DATA_DIR
    if not override and not _legacy_notice_shown:
        legacy_files = [FAILURES_FILE, ARCHIVE_FILE, LESSONS_FILE, "env-snapshot.json"]
        if any(os.path.isfile(os.path.join(LEGACY_DATA_DIR, name)) for name in legacy_files):
            print(
                f"env-tool-log: 检测到旧数据目录 {LEGACY_DATA_DIR}；"
                f"当前使用 {DEFAULT_DATA_DIR}。请审阅后迁移，或通过 ENV_TOOL_LOG_DIR 指定旧目录；"
                "未自动搬移、合并或读取旧数据。",
                file=sys.stderr,
            )
            _legacy_notice_shown = True
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


def write_entries(entries: list, path=None) -> None:
    with open(path or failures_path(), "w", encoding="utf-8") as f:
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
    for e in reversed(entries):
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
    def value(name, default=""):
        return entry.get(name) or (getattr(args, name + "_" if name == "from" else name, None) if args else None) or default

    category = value("category", "other")
    if category not in CATEGORIES:
        category = "other"
    incoming = {
        "cmd": str(cmd), "sig": str(sig).strip(), "category": category,
        "cause": value("cause"), "fix": value("fix"), "from": value("from", "codex"),
        "tool": value("tool") or str(cmd).split()[0],
    }
    entries = read_entries()
    archived = read_entries(archive_path())
    key = str(sig).strip().lower()
    matches = [e for e in archived + entries if (e.get("sig") or "").strip().lower() == key]
    if matches:
        current = dict(matches[-1])
        current["ts"] = matches[0].get("ts", now())
        current["count"] = sum(e.get("count", 1) for e in matches) + 1
        for old in reversed(matches):
            verified = old.get("verified_fix") or (old.get("fix") if old.get("status") == STATUS_FIXED else "")
            if verified:
                current["verified_fix"] = verified
                break
        for name, val in incoming.items():
            if val:
                current[name] = val
        current["status"] = STATUS_OPEN
        current["last_seen"] = now()
        entries = [e for e in entries if (e.get("sig") or "").strip().lower() != key]
        entries.append(current)
        write_entries(entries)
        if any((e.get("sig") or "").strip().lower() == key for e in archived):
            write_entries([e for e in archived if (e.get("sig") or "").strip().lower() != key], archive_path())
        lessons(apply=True)
        return {"duplicate": current}
    incoming.update(count=1, last_seen=now())
    added = append_entry(incoming)
    lessons(apply=True)
    return {"added": added}


def mark_fixed(sig: str, fix: str = "") -> int:
    entries = read_entries()
    updated = 0
    sig = (sig or "").strip().lower()
    for e in entries:
        if (e.get("sig") or "").strip().lower() == sig and e.get("status") == STATUS_OPEN:
            e["status"] = STATUS_FIXED
            e["ts_fixed"] = now()
            if fix:
                e["fix"] = fix
            if e.get("fix"):
                e["verified_fix"] = e["fix"]
            updated += 1
    if updated:
        write_entries(entries)
        lessons(apply=True)
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
            or p in (e.get("fix") or "").lower()
            or p in (e.get("verified_fix") or "").lower()
            or p in (e.get("tool") or "").lower()
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


def lessons(apply: bool = False, limit: int = 0) -> dict:
    latest = {}
    for entry in read_entries(archive_path()) + read_entries():
        key = (entry.get("sig") or "").strip().lower()
        if key:
            latest[key] = entry
    fixed = [e for e in latest.values()
             if e.get("verified_fix") or (e.get("status") == STATUS_FIXED and (e.get("fix") or "").strip())]
    if limit:
        fixed = fixed[-limit:]

    def inline(value):
        return " ".join(str(value or "").split())

    groups = {}
    for entry in fixed:
        tool = inline(entry.get("tool")) or inline(entry.get("cmd")).split(" ")[0] or "未分类"
        groups.setdefault(tool, []).append(entry)
    lines = ["## 工具经验索引", ""]
    for tool, entries in sorted(groups.items()):
        lines.extend([f"### {tool}", ""])
        for entry in entries:
            trigger = inline(entry.get("sig"))
            cause = inline(entry.get("cause"))
            fix = inline(entry.get("verified_fix") or entry.get("fix"))
            condition = trigger + ("；" + cause if cause else "")
            status = "（复发待复核）" if entry.get("status") == STATUS_OPEN else ""
            lines.append(f"- **触发条件**：{condition} → **做法**：{fix}{status}")
        lines.append("")
    if not fixed:
        lines.append("暂无包含已验证修复方法的记录。")
    snippet = "\n".join(lines) + "\n"
    if apply:
        lp = os.path.join(data_dir(), LESSONS_FILE)
        begin = "<!-- env-tool-log:lessons:start -->"
        end = "<!-- env-tool-log:lessons:end -->"
        previous = ""
        if os.path.exists(lp):
            with open(lp, encoding="utf-8") as f:
                previous = f.read()
        block = begin + "\n" + snippet + end
        start = previous.find(begin)
        finish = previous.find(end, start) if start >= 0 else -1
        if start >= 0 and finish >= 0:
            updated = previous[:start] + block + previous[finish + len(end):]
        else:
            updated = previous + ("\n\n" if previous else "") + block + "\n"
        with open(lp, "w", encoding="utf-8") as f:
            f.write(updated)
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
    p_add.add_argument("--tool", help="tool name, including built-in or MCP tools")
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
