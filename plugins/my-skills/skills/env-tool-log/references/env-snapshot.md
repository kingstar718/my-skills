# 环境快照

## 文件位置

- 默认 `~/.codex/skills-data/env-tool-log/env-snapshot.json`（环境变量 `ENV_TOOL_LOG_DIR` 可覆盖）。

## 生成与刷新

- `python scripts/snapshot_env.py`：重新探测并写盘。
- `python scripts/snapshot_env.py --stdout`：只输出 JSON 不写盘（供会话注入/hook）。
- `python scripts/snapshot_env.py --tools java,node,mvn`：只探测指定工具。

触发刷新的时机：装了新工具、升级了版本、PATH 变化、快照超过 30 天。

## 字段说明

| 字段 | 说明 |
|------|------|
| `ts` / `os` | 生成时间与系统信息 |
| `tools.<name>.path` | 可执行文件绝对路径（`shutil.which` 解析） |
| `tools.<name>.version` | 版本命令输出首行；失败时记录错误原文（不静默跳过） |
| `tools.<name>.error` | 探测失败原因（not found / exit code / timeout） |
| `env` | JAVA_HOME、GOPATH 等关键环境变量（仅记已设置的） |
| `path` | 完整 PATH 列表（用于判断工具解析顺序） |

## 使用约定

- 运行命令前若怀疑环境问题，先读快照对应工具条目；`error` 非空或 `path` 为 null 时按环境问题处理。
- 快照是"当时的"记录，工具升级后需重跑刷新，不要当实时数据用。
- 记录结果可直接用于失败日志的 cause 分析（如 java/javac 来自不同 JDK）。
