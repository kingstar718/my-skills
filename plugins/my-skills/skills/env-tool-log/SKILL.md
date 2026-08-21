---
name: env-tool-log
description: "Use when running shell commands, builds, dependency installs, environment configuration, or when a tool/command fails or behaves unexpectedly. Records the machine environment (JDK/Python/Node/npm/Maven versions and paths), logs tool-call failures with root causes to prevent repeating them, and provides tool-invocation rules for writing correct commands. Before executing, check tool rules → failure log → environment snapshot; after a failure, record it immediately. Works as Codex instructions and as Claude Code hooks."
---

# Env Tool Log

记录机器环境快照、工具调用失败日志和工具调用规则，避免重复踩坑。

## 核心流程

执行命令类任务时按顺序：

1. **查规则**：读 `references/tool-invocations.md`；若数据目录存在 `lessons.md`（由 `fail_log.py lessons --apply` 生成）一并读。
2. **查失败日志**：`python scripts/fail_log.py query "<命令关键词>"`，命中 OPEN 记录先看 cause/fix。
3. **查环境快照**：`python scripts/snapshot_env.py --stdout`（或读 `env-snapshot.json`），确认工具真实路径和版本。
4. **执行**：按规则的正确写法执行，设好超时。
5. **失败立即记录**：`python scripts/fail_log.py add --cmd "..." --sig "<关键错误>" [--category X]`；修复成功后 `mark-fixed --sig "..."`。

## 脚本

- `scripts/snapshot_env.py`：探测工具版本+路径 → `env-snapshot.json`。
- `scripts/fail_log.py`：`add` / `query` / `mark-fixed` / `prune` / `lessons`。
- `scripts/cc_hooks.py` + `scripts/install_cc_hooks.py`：Claude Code 自动捕获与提示（可选）。

## 引用文档（按需读）

- `references/tool-invocations.md`：工具调用规则（怎么写才对），含 `[BLOCK]` 高危规则。
- `references/env-snapshot.md`：快照字段与刷新时机。
- `references/failure-log.md`：记录字段、查询命令、生命周期、hook 说明。

## 数据目录

- 默认 `~/.codex/skills-data/env-tool-log/`，环境变量 `ENV_TOOL_LOG_DIR` 可覆盖。
- 快照/日志/教训是机器本机数据，不入库、不随技能分发。
