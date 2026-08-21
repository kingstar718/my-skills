# 失败日志

## 文件位置

- 记录：`~/.codex/skills-data/env-tool-log/failures.jsonl`（JSONL，一行一条）
- 归档：`failures-archive.jsonl`
- 教训：`lessons.md`

## 记录时机

- 失败当下立即记（不等重试成功）：上下文会压缩，跨轮次记忆不可靠；落盘一行几乎不占 token。
- 修复成功后用同一签名 `mark-fixed` 闭环；重复失败不重复记（同 sig 已有 OPEN 则跳过；已 FIXED 再失败视为复发，允许新记）。

## 字段

| 字段 | 说明 |
|------|------|
| ts | 记录时间 |
| cmd | 失败的命令/工具调用 |
| sig | 签名：命令+关键错误，用于去重与查询 |
| category | env / syntax / args / path / network / api / auth / other |
| cause | 根因（先记录后修复时初始可空） |
| fix | 修复方法 |
| status | OPEN / FIXED |
| from | codex / cc |
| ts_fixed | 修复时间（FIXED 时） |

## 命令

```bash
python scripts/fail_log.py add --cmd "..." --sig "..." [--cause C] [--fix F] [--category X] [--from src]
python scripts/fail_log.py add --stdin          # 读 JSON，hook 用
python scripts/fail_log.py query "关键词" [--all] [--limit N] [--json]
python scripts/fail_log.py mark-fixed --sig "..." [--fix F]
python scripts/fail_log.py prune [--older-days 90] [--max 500]
python scripts/fail_log.py lessons [--apply]
```

## 查询约定

- 执行命令前：`fail_log.py query "<命令关键词>"`，命中 OPEN 时按 cause/fix 处理或换写法。
- 会话开始（CC hook）会把环境快照摘要 + 未解决失败 + 教训注入上下文。

## Claude Code hooks

- `PostToolUse`（全部工具）：成功/失败都会触发，cc_hooks.py 读 transcript 最后一条 tool_result 的 `is_error` 判定失败，仅失败才记录；覆盖非 Bash 工具错误（如 Glob 超时）。
- `PreToolUse`（Bash）：命中 `[BLOCK]` 规则时 deny 并给原因。
- `SessionStart`：注入环境快照异常、未解决失败（最多 5 条）、教训（前 10 行）。
- `UserPromptSubmit`：提示词命中工具名时注入对应规则。
- 安装：`python scripts/install_cc_hooks.py`（写 `~/.claude/settings.json`，使用绝对路径，不依赖 CLAUDE_PLUGIN_ROOT）；`--print` 预览；`--uninstall` 移除；`--scope project` 写项目级 `.claude/settings.local.json`。
- `PostToolUseFailure` 并非官方事件（官方列表无此项），注册仅为兼容可能支持它的版本；与 `PostToolUse` 双触发时同 sig 去重防双写。

## 隐私

- 不记录密钥/密码/内网敏感地址；数据目录不在 git 内，但公开分享前仍建议检查。
