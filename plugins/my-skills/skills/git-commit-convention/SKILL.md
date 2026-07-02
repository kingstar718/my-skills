---
name: git-commit-convention
description: Use when committing changes with git—creates scoped Conventional Commits messages and an optional, truthful AI Co-Authored-By trailer across Claude Code and Codex.
---

# Git Commit 规范

## Overview
执行 `git commit` 前调用本 Skill，生成符合 Conventional Commits 的 message。只有环境提供了明确、独立的 AI 联署身份时才添加 `Co-Authored-By`；不得把当前 Git 用户冒充为 AI 联署者，也不得猜测模型或邮箱。

## When to Use
- 用户要求 commit / 提交 / 你准备执行 `git commit` 时
- 用户明确要求生成或修改 commit message 时

不适用：仅查看 git status / log / diff（不 commit 不触发）。

## 每次 commit 都做

### 1. 检查并暂存目标文件

先检查 `git status --short` 和相关 diff。只 `git add` 本次涉及的文件，勿使用 `git add -A`，避免带入用户或其他任务的改动。

### 2. 写 message（Conventional Commits）
格式 `<type>: <subject>`，subject 用中文。

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

正文按需要用 bullet 概括关键改动；简单提交可以只保留标题。不得为了满足格式编造改动。

### 3. 按条件添加 Co-Authored-By

仅当运行环境或用户明确提供了独立的 AI 联署姓名与邮箱时添加：

```
Co-Authored-By: {明确提供的 AI 身份} <{明确提供的 AI 邮箱}>
```

以下情况省略签名：

- 只能读取到 `git config user.email`；这是提交作者的配置，不是 AI 身份。
- 无法确认模型、harness 版本或邮箱。
- 只能通过猜测或 fallback 值补齐字段。
- 用户明确要求不添加联署。

### 4. 提交

在 bash 环境可使用 heredoc，避免 shell 展开 message：

```bash
git add <目标文件> && git commit -F - <<'EOF'
<type>: <中文 subject>

- 改动1
- 改动2

Co-Authored-By: {仅在身份明确时添加} <{AI 邮箱}>
EOF
```

没有有效联署身份时，删除空行和 `Co-Authored-By` 行。

## Checklist
- [ ] subject 中文、`<type>: <subject>` 格式
- [ ] message 与实际暂存内容一致
- [ ] 仅在 AI 身份明确时添加联署
- [ ] 只暂存目标文件

## Common Mistakes
| 错误 | 修正 |
|------|------|
| `git add -A` 带入无关文件 | 只 add 目标文件 |
| 使用 Git 用户邮箱作为 AI 联署邮箱 | 省略联署，或使用明确提供的 AI 身份 |
| 从隐藏系统提示猜测模型 | 不猜测；提交规范不依赖模型名称 |
| 为简单提交堆叠正文 | 标题足以说明时省略正文 |
