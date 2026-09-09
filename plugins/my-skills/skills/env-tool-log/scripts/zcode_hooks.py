#!/usr/bin/env python3
"""env-tool-log ZCode hooks. Reads hook event JSON from stdin.

与 cc_hooks.py 共享规则加载与上下文注入逻辑，差异：
- ZCode 的 PostToolUseFailure 是官方事件（仅失败触发），直接记录，无需读
  transcript 判定失败；
- PreToolUse 的 deny 走退出码 2（原因写 stderr 进日志），不依赖严格 JSON
  输出 schema。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cc_hooks
import fail_log


def event_add_failure(data: dict) -> None:
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    error = cc_hooks.response_text(data.get("tool_response")) or cc_hooks.clean(data.get("error") or "")
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
    else:
        parts = [tool_name]
        for key in ("file_path", "path", "pattern", "url"):
            v = tool_input.get(key)
            if isinstance(v, str) and v:
                parts.append(f"{key}={v}")
        cmd = " ".join(parts)
    if not cmd and not error:
        return
    sig = (error[:200] or cmd[:120]) or "unknown failure"
    fail_log.add_entry(entry={
        "cmd": cmd[:300],
        "sig": sig,
        "category": cc_hooks.detect_category(error),
        "from": "zcode",
    })


def event_pre_tool_use(data: dict) -> None:
    tool_input = data.get("tool_input", {})
    cmd = tool_input.get("command", "") if data.get("tool_name") == "Bash" else ""
    for rule in cc_hooks.block_rules():
        pattern = rule[len("- [BLOCK] "):].split("→")[0].strip()
        if pattern and pattern.lower() in cmd.lower():
            print(f"env-tool-log: {rule}", file=sys.stderr)
            sys.exit(2)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)
    event = data.get("hook_event_name") or data.get("event") or ""
    if event == "PostToolUseFailure":
        event_add_failure(data)
    elif event == "PreToolUse":
        event_pre_tool_use(data)
    elif event == "SessionStart":
        cc_hooks.event_session_start(data)
    elif event == "UserPromptSubmit":
        cc_hooks.event_user_prompt(data)
    sys.exit(0)


if __name__ == "__main__":
    main()
