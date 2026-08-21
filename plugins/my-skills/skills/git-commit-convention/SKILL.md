---
name: git-commit-convention
description: Use when the user asks to create, revise, or execute a Git commit. Generates an accurate Conventional Commit message and only stages or commits files when explicitly requested.
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

标题格式为 `<type>: <subject>`，默认不带 scope；仅当同一次改动需要明确区分模块（如同时涉及前端/后端/CI）时添加 `<type>(scope): <subject>`。

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

subject 默认使用中文，`type` 保持英文；仅当用户明确要求其他语言时切换。**默认单行提交**：写完标题直接结束，不追加正文（因此也没有空行）。仅当用户明确要求说明、或确有多个关键改动需要记录时，才用简短中文 bullet 正文。不得编造 diff 中不存在的内容。

## 提交粒度

- 同一逻辑变更（如同一问题修复、同一功能的多文件调整）默认合并为一个提交，不做过程性小提交。
- 未推送的同主题提交，可建议 `git commit --amend` 合并（执行前仍须用户确认）。
- 用户明确要求拆分提交时按用户要求执行。

## AI 使用信息（可选）

默认不写入任何 AI 相关脚注，保持提交信息简洁。仅当用户明确要求记录 AI 信息时，在 message 末尾追加一行：

```text
AI-Generated-By: <Agent 名称及版本> / <模型>
```

获取方式以当前会话/生效配置为准，无法可靠获取时写 `unknown`。Git 的 Author 已使用仓库配置的用户名和邮箱，因此不添加 `Co-Authored-By`，也不重复写入 Git 用户身份。
