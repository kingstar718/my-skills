#!/usr/bin/env python3
"""Install env-tool-log Claude Code hooks (absolute paths, no CLAUDE_PLUGIN_ROOT dependency)."""
import argparse
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
CC_HOOKS_SCRIPT = PLUGIN_ROOT / "skills" / "env-tool-log" / "scripts" / "cc_hooks.py"
MARKER = "env-tool-log/scripts/cc_hooks.py"


def build_hooks(python_exe: str) -> dict:
    cmd = f'"{python_exe}" "{CC_HOOKS_SCRIPT}"'
    return {
        # PostToolUse 对成功/失败都触发（含 Bash 非零退出），matcher 留空覆盖
        # 全部工具（Glob 超时等非 Bash 失败也能捕获），由 cc_hooks.py 依据
        # transcript 的 tool_result.is_error 过滤出失败。
        "PostToolUse": [{"hooks": [{"type": "command", "command": cmd}]}],
        # 官方事件列表无 PostToolUseFailure，注册仅为兼容可能支持它的版本。
        "PostToolUseFailure": [{"matcher": "Bash", "hooks": [{"type": "command", "command": cmd}]}],
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": cmd}]}],
        "SessionStart": [{"hooks": [{"type": "command", "command": cmd}]}],
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": cmd}]}],
    }


def settings_path(scope: str) -> Path:
    if scope == "project":
        return Path.cwd() / ".claude" / "settings.local.json"
    return Path.home() / ".claude" / "settings.json"


def strip_ours(obj: dict) -> dict:
    hooks = obj.get("hooks") or {}
    def is_ours(group: dict) -> bool:
        return any(
            MARKER in (h.get("command", "") or "").replace("\\", "/")
            for h in group.get("hooks", [])
        )
    for event, groups in list(hooks.items()):
        hooks[event] = [
            g for g in groups if not is_ours(g)
        ]
        if not hooks[event]:
            del hooks[event]
    if not hooks:
        obj.pop("hooks", None)
    return obj


def merge_hooks(obj: dict, new_hooks: dict) -> dict:
    hooks = obj.setdefault("hooks", {})
    for event, groups in new_hooks.items():
        hooks.setdefault(event, []).extend(groups)
    return obj


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="install/remove env-tool-log Claude Code hooks")
    ap.add_argument("--print", action="store_true", help="print hooks config and exit")
    ap.add_argument("--uninstall", action="store_true", help="remove our hooks from settings")
    ap.add_argument("--scope", choices=["user", "project"], default="user")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    new_hooks = build_hooks(args.python)
    if args.print:
        print(json.dumps(new_hooks, ensure_ascii=False, indent=2))
        return

    path = settings_path(args.scope)
    obj = {}
    if path.exists():
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            obj = {}
    obj = strip_ours(obj)
    if args.uninstall:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Removed env-tool-log hooks from {path}")
        return
    merge_hooks(obj, new_hooks)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Installed env-tool-log hooks into {path}")


if __name__ == "__main__":
    main()
