#!/usr/bin/env python3
"""env-tool-log Claude Code hooks. Reads hook event JSON from stdin."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fail_log

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
RULES_FILE = PLUGIN_ROOT / "skills" / "env-tool-log" / "references" / "tool-invocations.md"

TOOL_NAMES = [
    "java", "javac", "python", "py", "node", "npm", "pnpm", "yarn", "mvn",
    "gradle", "git", "docker", "go", "rustc", "cargo", "dotnet", "gcc",
    "cmake", "make", "ruby", "perl", "php", "kubectl", "terraform",
    "pwsh", "powershell", "rg", "grep",
]

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def clean(text) -> str:
    return ANSI.sub("", text or "").strip()


def detect_category(error: str) -> str:
    e = (error or "").lower()
    if any(k in e for k in ["no such file", "找不到指定的文件", "cannot find the file", "path not found"]):
        return "path"
    if any(k in e for k in ["command not found", "not recognized", "不是内部或外部命令", "cannot find"]):
        return "env"
    if any(k in e for k in ["invalid option", "unrecognized argument", "无效的标记", "unknown option", "语法错误"]):
        return "syntax"
    if any(k in e for k in ["missing required argument", "expected one argument", "requires an argument", "unexpected argument"]):
        return "args"
    if any(k in e for k in ["timed out", "timeout", "unreachable", "proxy", "ssl", "connect"]):
        return "network"
    if any(k in e for k in ["authentication", "unauthorized", "401", "403", "login"]):
        return "auth"
    return "other"


def load_rules():
    rules = []  # (section, line)
    if RULES_FILE.exists():
        section = ""
        for line in RULES_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("## "):
                section = line[3:].strip().lower()
            elif line.strip().startswith("- "):
                rules.append((section, line.strip()))
    return rules


def block_rules():
    return [ln for _, ln in load_rules() if ln.startswith("- [BLOCK]")]


def response_text(tool_response) -> str:
    """tool_response 可能是 dict（Bash 为 stdout/stderr）或字符串，统一提取文本。"""
    if isinstance(tool_response, dict):
        parts = []
        for key in ("error", "stderr", "stdout"):
            v = tool_response.get(key)
            if isinstance(v, str) and v.strip():
                parts.append(clean(v))
        return " ".join(parts)
    if isinstance(tool_response, str):
        return clean(tool_response)
    return ""


def is_last_tool_result_error(transcript_path) -> bool:
    """读 transcript 尾部，返回最后一条 tool_result 的 is_error。

    hook 输入的 tool_response 无可靠失败标志，transcript JSONL 的
    tool_result 条目带 is_error；读取失败一律按非失败处理（宁漏勿误记）。
    """
    if not transcript_path:
        return False
    try:
        with open(transcript_path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 65536))
            tail = f.read().decode("utf-8", errors="replace")
    except OSError:
        return False
    for line in reversed(tail.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (entry.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_result":
                return bool(item.get("is_error"))
    return False


def event_add_failure(data: dict) -> None:
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    error = response_text(data.get("tool_response")) or clean(data.get("error") or "")
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
        "category": detect_category(error),
        "from": "cc",
    })


def event_post_tool_use(data: dict) -> None:
    """PostToolUse 对成功/失败都触发：先判失败，仅失败才记录。"""
    tool_response = data.get("tool_response")
    if isinstance(tool_response, dict) and (tool_response.get("is_error") or tool_response.get("error")):
        failed = True
    else:
        failed = is_last_tool_result_error(data.get("transcript_path"))
    if failed:
        event_add_failure(data)


def event_pre_tool_use(data: dict) -> None:
    tool_input = data.get("tool_input", {})
    if data.get("tool_name") != "Bash":
        return
    cmd = tool_input.get("command", "")
    for rule in block_rules():
        pattern = rule[len("- [BLOCK] "):].split("→")[0].strip()
        if pattern and pattern.lower() in cmd.lower():
            out = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"env-tool-log: {rule}",
                }
            }
            print(json.dumps(out, ensure_ascii=False))
            return


def event_session_start(data: dict) -> None:
    ctx = []
    snap_path = os.path.join(fail_log.data_dir(), "env-snapshot.json")
    if os.path.exists(snap_path):
        try:
            snap = json.loads(open(snap_path, encoding="utf-8").read())
            issues = []
            for name, info in snap.get("tools", {}).items():
                if not info.get("path"):
                    issues.append(f"{name}: 未安装")
                elif info.get("error"):
                    issues.append(f"{name}: {info.get('error')}")
            if issues:
                ctx.append("环境快照异常： " + "；".join(issues[:8]))
        except (json.JSONDecodeError, OSError):
            pass
    open_entries = fail_log.query(limit=5)
    if open_entries:
        ctx.append("未解决失败日志（最新 5 条）：")
        for e in open_entries:
            ctx.append(f"- {e.get('cmd')} | {e.get('sig')[:80]}")
    lessons_path = os.path.join(fail_log.data_dir(), "lessons.md")
    if os.path.exists(lessons_path):
        lines = [ln for ln in open(lessons_path, encoding="utf-8").read().splitlines() if ln.strip()][:10]
        if lines:
            ctx.append("历史教训（前 10 行）：")
            ctx.extend(lines)
    if not ctx:
        return
    context = "\n".join(ctx)
    if len(context) > 1200:
        context = context[:1200] + "\n…（截断）"
    out = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "env-tool-log 会话上下文：\n" + context,
        }
    }
    print(json.dumps(out, ensure_ascii=False))


def event_user_prompt(data: dict) -> None:
    prompt = (data.get("prompt") or "").lower()
    if not prompt:
        return
    matched = []
    for section, line in load_rules():
        if line.startswith("- [BLOCK]"):
            continue
        toks = [t for t in TOOL_NAMES if t in line.lower() or t in section]
        if any(t in prompt for t in toks):
            matched.append(line)
    if matched:
        ctx = "工具调用提示（env-tool-log）：\n" + "\n".join(matched[:8])
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx,
            }
        }
        print(json.dumps(out, ensure_ascii=False))


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)
    event = data.get("hook_event_name", "")
    if event == "PostToolUse":
        event_post_tool_use(data)
    elif event == "PostToolUseFailure":
        # 官方事件列表无此事件；若某版本支持则直接记录，同 sig 去重防双写
        event_add_failure(data)
    elif event == "PreToolUse":
        event_pre_tool_use(data)
    elif event == "SessionStart":
        event_session_start(data)
    elif event == "UserPromptSubmit":
        event_user_prompt(data)
    sys.exit(0)


if __name__ == "__main__":
    main()
