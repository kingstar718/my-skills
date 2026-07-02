---
name: git-commit-convention
description: Use when the user asks to create, revise, or execute a Git commit. Generates an accurate Conventional Commit message, records the active AI agent and model, and only stages or commits files when explicitly requested.
---

# Git Commit 规范

## 工作模式

- 用户只要求生成或修改 commit message：检查相关 diff 后返回 message，不暂存、不提交。
- 用户明确要求执行提交：按下述流程检查、暂存并提交。

不要把“生成 commit message”视为执行提交的授权。

## 执行流程

1. 运行 `git status --short`，检查相关的工作区 diff 和 `git diff --cached`。
2. 明确本次提交应包含哪些文件，并确保 message 只描述这些改动。
3. 如果已有与本次任务无关的暂存内容，保留原状并停止提交，请用户决定是一起提交还是先拆分。
4. 仅在用户要求执行提交时，逐项 `git add <目标文件>`；不得使用 `git add -A` 或 `git add .`。
5. 再次检查 `git diff --cached`，确认实际暂存内容与 message 一致后执行 `git commit`。
6. 返回 commit hash 和标题；提交失败时返回原始错误及可行的处理建议。

除非用户明确要求，否则不得执行 `git commit --amend`、`git push` 或使用 `--no-verify` 跳过 hooks。

## Message 格式

标题格式为 `<type>[(scope)]: <subject>`。仅当 scope 明确且有助于区分改动时添加。

| type | 场景 |
|------|------|
| feat | 新功能、新特性 |
| fix | Bug 修复 |
| docs | 文档变更 |
| refactor | 重构（不改功能、不修 bug） |
| chore | 构建/依赖/配置等杂项 |
| test | 添加或修改测试 |
| style | 格式调整（不影响逻辑） |
| perf | 性能优化 |

subject 遵循仓库近期提交使用的语言；无法判断时使用中文。标题足以准确表达时省略正文，否则用简短 bullet 说明关键改动。不得编造 diff 中不存在的内容。

## AI 使用信息

在 message 末尾追加一行：

```text
AI-Generated-By: <Agent 名称及版本> / <模型>
```

首次需要生成该行时，主动获取实际参与当前会话的 Agent、Agent 版本和模型，并在本次会话中记住结果。后续提交直接复用，不重复运行版本命令或读取配置。出现以下情况时重新获取：

- 开始了新会话。
- 用户切换了模型或 Agent。
- 当前环境明确表明版本或模型已变化。
- 用户要求刷新 AI 使用信息。

按当前运行环境选择探测方式：

- Codex：Agent 记为 `Codex CLI`，使用 `codex --version` 获取版本；模型优先使用当前会话信息，其次读取当前生效的 Codex 配置。
- Claude Code：Agent 记为 `Claude Code`，使用 `claude --version` 获取版本；模型优先使用当前会话信息，其次读取当前生效的 Claude Code 配置。
- 其他 Agent：使用运行环境明确提供的名称和模型；优先通过该 Agent 自身的版本命令获取版本，其次读取其当前生效配置。

不得根据产品默认值猜测。某一项无法可靠获取时写 `unknown`，不要用其他工具、Git 用户身份或推测值补齐。会话缓存只保留在当前对话上下文中，不写入仓库或全局配置。

示例：

```text
AI-Generated-By: Codex CLI 0.142.4 / gpt-5.5
```

Git 的 Author 已使用当前仓库配置的用户名和邮箱，因此不添加 `Co-Authored-By`，也不重复写入 Git 用户身份。
