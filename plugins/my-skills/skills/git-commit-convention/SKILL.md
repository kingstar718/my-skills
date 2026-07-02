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

只有用户或运行环境明确提供独立的 AI 姓名和邮箱时才添加 `Co-Authored-By`；不得使用 Git 用户身份，也不得猜测模型、姓名或邮箱。
