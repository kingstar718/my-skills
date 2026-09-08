#!/usr/bin/env python3
"""env-tool-log: cross-platform environment snapshot (versions + paths)."""
import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fail_log

TOOLS = {
    "java": ["-version"],
    "javac": ["-version"],
    "python": ["--version"],
    "py": ["--version"],
    "node": ["--version"],
    "npm": ["--version"],
    "pnpm": ["--version"],
    "yarn": ["--version"],
    "mvn": ["--version"],
    "gradle": ["--version"],
    "git": ["--version"],
    "docker": ["--version"],
    "go": ["version"],
    "rustc": ["--version"],
    "cargo": ["--version"],
    "dotnet": ["--version"],
    "gcc": ["--version"],
    "cmake": ["--version"],
    "make": ["--version"],
    "ruby": ["--version"],
    "perl": ["--version"],
    "php": ["--version"],
    "kubectl": ["version", "--client"],
    "terraform": ["version"],
    "powershell": ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
    "pwsh": ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"],
}

ENV_VARS = [
    "JAVA_HOME", "JDK_HOME", "GRADLE_HOME", "MAVEN_HOME", "M2_HOME",
    "ANDROID_HOME", "GOPATH", "GOROOT", "PYTHONPATH", "NODE_PATH", "DOCKER_HOST",
]

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def clean(text: str) -> str:
    text = ANSI.sub("", text or "").strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return lines[0] if lines else ""


def run_version(name: str, args: list) -> dict:
    try:
        if os.name == "nt":
            cmd = f"{name} {' '.join(args)}"
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, errors="replace")
        else:
            r = subprocess.run([name] + args, capture_output=True, text=True, timeout=15, errors="replace")
        out = clean(r.stdout) or clean(r.stderr)
        if r.returncode == 0 and out:
            return {"version": out[:200]}
        return {"version": out[:200], "error": f"exit {r.returncode}"}
    except FileNotFoundError:
        return {"version": None, "error": "not found"}
    except subprocess.TimeoutExpired:
        return {"version": None, "error": "timeout"}


def _local_repo_from_settings(settings_path: str):
    try:
        with open(settings_path, encoding="utf-8", errors="replace") as f:
            m = re.search(r"<localRepository>\s*([^<]+?)\s*</localRepository>", f.read())
            if m:
                return os.path.expanduser(os.path.expandvars(m.group(1).strip()))
    except OSError:
        pass
    return None


def maven_local_repository():
    """探测 Maven 本地仓库：user settings.xml 优先，其次 MAVEN_HOME/M2_HOME
    conf/settings.xml，最后默认位置。机器级路径只用于本机快照，不写死进共享规则。"""
    home = os.path.expanduser("~")
    user_profile = os.environ.get("USERPROFILE", home)
    candidates = []
    if os.name == "nt":
        candidates.append(os.path.join(user_profile, ".m2", "settings.xml"))
    candidates.append(os.path.join(home, ".m2", "settings.xml"))
    m2 = os.environ.get("MAVEN_HOME") or os.environ.get("M2_HOME")
    if m2:
        candidates.append(os.path.join(m2, "conf", "settings.xml"))
    for settings in candidates:
        if os.path.exists(settings):
            repo = _local_repo_from_settings(settings)
            if repo:
                return repo
    default = os.path.join(user_profile, ".m2", "repository") if os.name == "nt" \
        else os.path.join(home, ".m2", "repository")
    return default if os.path.isdir(default) else None


def probe(tools: list) -> dict:
    result = {"tools": {}}
    for name in tools:
        path = shutil.which(name)
        if not path:
            result["tools"][name] = {"path": None, "version": None, "error": "not found"}
            continue
        info = run_version(name, TOOLS.get(name, ["--version"]))
        info["path"] = path
        result["tools"][name] = info
    env = {var: os.environ[var] for var in ENV_VARS if os.environ.get(var)}
    result["env"] = env
    result["maven"] = {"localRepository": maven_local_repository()}
    result["path"] = os.environ.get("PATH", "").split(os.pathsep)
    return result


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="snapshot_env.py", description="env-tool-log environment snapshot")
    ap.add_argument("--tools", default="", help="comma-separated tool list override")
    ap.add_argument("--stdout", action="store_true", help="print JSON to stdout, do not write file")
    args = ap.parse_args()

    tools = [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools else list(TOOLS)
    data = probe(tools)
    data["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["os"] = {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }

    if args.stdout:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    path = os.path.join(fail_log.data_dir(), "env-snapshot.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    missing = [k for k, v in data["tools"].items() if not v.get("path")]
    print(f"Snapshot written to {path}")
    print(f"tools: {len(data['tools'])} | missing: {len(missing)} ({', '.join(missing) or 'none'})")


if __name__ == "__main__":
    main()
