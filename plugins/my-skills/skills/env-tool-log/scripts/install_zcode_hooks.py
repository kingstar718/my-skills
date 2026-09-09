#!/usr/bin/env python3
"""Install env-tool-log ZCode hooks (config-file hooks, absolute paths)."""
import argparse
import json
import sys
from pathlib import Path

ZCODE_HOOKS_SCRIPT = Path(__file__).resolve().with_name("zcode_hooks.py")
MARKER = "env-tool-log/scripts/zcode_hooks.py"
TIMEOUT_MS = 15000


def build_hook(python_exe: str) -> dict:
    # process 型走参数向量不经 shell，Windows 下比 shell 字符串稳
    return {
        "type": "process",
        "command": python_exe,
        "args": [str(ZCODE_HOOKS_SCRIPT)],
        "timeoutMs": TIMEOUT_MS,
    }


def build_events(python_exe: str) -> dict:
    h = build_hook(python_exe)
    return {
        # ZCode 官方事件：仅工具失败时触发，直接记录（from=zcode）
        "PostToolUseFailure": [{"hooks": [h]}],
        # matcher 为大小写敏感正则，匹配工具名
        "PreToolUse": [{"matcher": "Bash", "hooks": [h]}],
        "SessionStart": [{"hooks": [h]}],
        "UserPromptSubmit": [{"hooks": [h]}],
    }


def config_path(scope: str) -> Path:
    if scope == "workspace":
        return Path.cwd() / ".zcode" / "config.json"
    return Path.home() / ".zcode" / "cli" / "config.json"


def is_our_hook(hook: dict) -> bool:
    fields = [str(hook.get("command", ""))] + [str(a) for a in hook.get("args", [])]
    return any(MARKER in f.replace("\\", "/") for f in fields)


def strip_ours(obj: dict) -> dict:
    hooks = obj.get("hooks") or {}
    events = hooks.get("events") or {}

    def is_ours(group: dict) -> bool:
        return any(is_our_hook(h) for h in group.get("hooks", []))

    for event, groups in list(events.items()):
        events[event] = [g for g in groups if not is_ours(g)]
        if not events[event]:
            del events[event]
    if events:
        hooks["events"] = events
    else:
        hooks.pop("events", None)
        # 事件已空则连 enabled 一起移除，恢复未安装状态
        hooks.pop("enabled", None)
    if hooks:
        obj["hooks"] = hooks
    else:
        obj.pop("hooks", None)
    return obj


def merge_hooks(obj: dict, new_events: dict) -> dict:
    hooks = obj.setdefault("hooks", {})
    # 配置文件 hooks 默认禁用，必须显式开启
    hooks["enabled"] = True
    events = hooks.setdefault("events", {})
    for event, groups in new_events.items():
        events.setdefault(event, []).extend(groups)
    return obj


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="install/remove env-tool-log ZCode hooks")
    ap.add_argument("--print", action="store_true", help="print hooks config and exit")
    ap.add_argument("--uninstall", action="store_true", help="remove our hooks from config")
    ap.add_argument("--scope", choices=["user", "workspace"], default="user",
                    help="user 写 ~/.zcode/cli/config.json，workspace 写 <cwd>/.zcode/config.json")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    new_events = build_events(args.python)
    if args.print:
        print(json.dumps({"hooks": {"enabled": True, "events": new_events}},
                         ensure_ascii=False, indent=2))
        return

    path = config_path(args.scope)
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
    merge_hooks(obj, new_events)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Installed env-tool-log hooks into {path}")
    print("新建会话后生效；卸载：--uninstall")


if __name__ == "__main__":
    main()
