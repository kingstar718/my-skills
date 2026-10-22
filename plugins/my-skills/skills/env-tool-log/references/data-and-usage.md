# 数据与使用

## 数据目录

默认使用 `~/.my-skills/env-tool-log/`；显式配置的 `ENV_TOOL_LOG_DIR` 优先。
快照、日志与经验索引共用该目录，各 harness 保持相同配置，会话中不静默切换。

| 文件 | 用途 |
| --- | --- |
| `env-snapshot.json` | 工具路径、版本与环境快照 |
| `failures.jsonl` | 按签名维护的当前错误记录，JSONL 格式 |
| `failures-archive.jsonl` | 已归档记录，仍可提供预防教训 |
| `lessons.md` | 按工具分类的经验索引与手工正文 |

## 旧目录与迁移

旧默认目录为 `~/.codex/skills-data/env-tool-log/`。
未配置环境变量且检测到其中有日志、快照或教训时，脚本每个进程最多提示一次；
提示写入 stderr，stdout 的 JSON 格式保持不变。

- **沿用旧目录**：显式设置 `ENV_TOOL_LOG_DIR`，各 harness 使用相同配置。
- **迁移到共享目录**：先检查旧目录和新目录内容，再迁移所需文件；
  两边都有数据时先审阅差异，不覆盖或盲目拼接。
- **生效范围**：脚本不自动搬移、合并或读取旧数据，也不修改其他客户端的环境变量；
  迁移完成后，各 harness 统一使用新目录，或统一显式指定同一目录。

## 环境快照

### 生成与刷新

- `python scripts/snapshot_env.py`：重新探测并写盘。
- `python scripts/snapshot_env.py --stdout`：只输出 JSON 不写盘（供会话注入/hook）。
- `python scripts/snapshot_env.py --tools java,node,mvn`：只探测指定工具。

触发刷新的时机：装了新工具、升级了版本、PATH 变化、快照超过 30 天。

### 字段说明

| 字段 | 说明 |
|------|------|
| `ts` / `os` | 生成时间与系统信息 |
| `tools.<name>.path` | 可执行文件绝对路径（`shutil.which` 解析） |
| `tools.<name>.version` | 版本命令输出首行；失败时记录错误原文（不静默跳过） |
| `tools.<name>.error` | 探测失败原因（not found / exit code / timeout） |
| `env` | JAVA_HOME、GOPATH 等关键环境变量（仅记已设置的） |
| `maven.localRepository` | Maven 本地仓库绝对路径（探测 user/全局 settings.xml 的 `<localRepository>`，缺省回退默认位置；机器级，勿写死进共享规则） |
| `path` | 完整 PATH 列表（用于判断工具解析顺序） |

### 使用约定

- 运行命令前若怀疑环境问题，先读快照对应工具条目；`error` 非空或 `path` 为 null 时按环境问题处理。
- 快照是"当时的"记录，工具升级后需重跑刷新，不要当实时数据用。
- 记录结果可直接用于失败日志的 cause 分析（如 java/javac 来自不同 JDK）。

## 记录与闭环

- **记录范围**：记录可复用的命令、参数、路径和环境故障；
  预期 TDD 红灯、正常无匹配和业务断言留在任务验证中。
- **唯一记录**：签名忽略首尾空格与大小写，同签名只维护一条当前记录；
  重复登记更新 `count`、`last_seen` 与状态，已归档记录复发时恢复到活动日志。
  命中旧重复记录时仅合并该签名，不批量改写其他历史数据。
- **稳定签名**：工具名与稳定错误特征组成签名，不带动态对象值；
  已有同类记录复用原签名，脚本不自动识别不同描述是否属于同一根因。
- **状态与修复**：复发时重新 OPEN，保存上次已验证方法；
  `mark-fixed` 只关闭 OPEN 并更新已验证方法，不把候选方法提升为预防规则。
  关闭记录不删除教训，新增和关闭时自动同步索引。
- **自动捕获**：hooks 无法判断全部业务上下文，使用方需核对误记；
  不把预期失败标成一条已验证的工具修复。
- **日志故障**：先修正脚本调用，不递归记录日志工具自身的故障。

## 日志字段

| 字段 | 说明 |
|------|------|
| ts | 首次记录时间 |
| tool | 工具名，包括内置工具与 MCP；未传时取 cmd 首个词 |
| count / last_seen | 登记次数 / 最近出现时间，旧记录缺少次数时按1计算 |
| cmd | 失败的命令/工具调用 |
| sig | 签名：命令+关键错误，用于去重与查询 |
| category | env / syntax / args / path / network / api / auth / other |
| cause | 根因（先记录后修复时初始可空） |
| fix | 当前修复方法或候选方案 |
| verified_fix | 上次经 mark-fixed 确认的方法，复发仍保留 |
| status | OPEN / FIXED |
| from | 记录来源，如 codex / cc / zcode / pi；手工调用应显式传入，旧默认 codex 保留兼容 |
| ts_fixed | 最近一次验证修复的时间，复发后可保留 |

## 日志命令

```bash
python scripts/fail_log.py add --cmd "..." --sig "..." [--tool TOOL] [--cause C] [--fix F] [--category X] [--from src]
python scripts/fail_log.py add --stdin          # 读 JSON，hook 用
python scripts/fail_log.py query "关键词" [--all] [--limit N] [--json]
python scripts/fail_log.py mark-fixed --sig "..." [--fix F]
python scripts/fail_log.py prune [--older-days 90] [--max 500]
python scripts/fail_log.py lessons [--apply]
```

## 查询与教训

- **执行前查询**：首次使用或环境变化时，使用 `query "关键词" --all --limit 5`；
  搜索工具、命令、签名、原因、候选与已验证修复。命中内容需与当前环境核对。
- **兼容行为**：`query` 默认仍只返回 OPEN；`--all` 包含 FIXED，保留原有结果顺序。
  同一会话内复用相关结论，不为每条命令重复查询。
- **经验索引**：`lessons` 从活动日志和归档中按签名取当前已验证做法，按工具分类，
  默认输出完整索引。签名同时作为日志关联标识；有已验证方法的复发条目标注待复核。
  未验证的候选方案不进入预防规则，归档不移除有效教训。
- **教训写入**：`lessons --apply` 更新 `env-tool-log:lessons` 自动区块，保留手工正文；
  新增、复发或关闭记录会自动更新索引；不追加同类教训，旧版未标记正文需另行审阅。
- **会话注入**：CC hook 注入环境快照摘要、未解决失败与教训；
  Codex 使用上述按需检查规则，不假设已有自动注入。

## Claude Code hooks

- `PostToolUse`（全部工具）：成功/失败都会触发，cc_hooks.py 读 transcript 最后一条 tool_result 的 `is_error` 判定失败，仅失败才记录；覆盖非 Bash 工具错误（如 Glob 超时）。
- `PreToolUse`（Bash）：命中 `[BLOCK]` 规则时 deny 并给原因。
- `SessionStart`：注入环境快照异常、未解决失败（最多 5 条）、教训（前 10 行）。
- `UserPromptSubmit`：提示词命中工具名时注入对应规则。
- 安装：`python scripts/install_cc_hooks.py`（写 `~/.claude/settings.json`，使用绝对路径，不依赖 CLAUDE_PLUGIN_ROOT）；`--print` 预览；`--uninstall` 移除；`--scope project` 写项目级 `.claude/settings.local.json`。
- `PostToolUseFailure` 并非官方事件（官方列表无此项），注册仅为兼容可能支持它的版本；与 `PostToolUse` 双触发时同 sig 更新同一记录；count 表示登记次数，不保证等于实际命令次数。

## ZCode hooks

- 配置位置：`~/.zcode/cli/config.json` → `hooks.events`（结构 `{ enabled, events: { <Event>: [{ matcher?, hooks }] } }`），配置文件 hooks 默认禁用，安装脚本会写 `hooks.enabled: true`。
- `PostToolUseFailure`（全部工具）：ZCode 官方事件，仅失败时触发，直接记录（`from=zcode`），无需像 Claude 那样读 transcript 判定。
- `PreToolUse`（matcher `Bash`，大小写敏感正则）：命中 `[BLOCK]` 规则时退出码 2 deny，原因写 stderr；不走 JSON 输出，规避严格 schema 校验。
- `SessionStart` / `UserPromptSubmit`：注入内容同 Claude 版；输出用 Claude 兼容 envelope（`hookSpecificOutput.additionalContext`），若客户端日志报 schema 校验失败需按实际支持的键调整。
- hook 用 `type: "process"`（参数向量不经 shell），Windows 下避免 shell 转义问题。
- 安装：`python scripts/install_zcode_hooks.py`（写 `~/.zcode/cli/config.json`，绝对路径）；`--print` 预览；`--uninstall` 移除；`--scope workspace` 写项目级 `.zcode/config.json`。新建会话后生效。

## 隐私

- 不记录密钥/密码/内网敏感地址；数据目录不在 git 内，但公开分享前仍建议检查。
