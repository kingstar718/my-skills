---
name: git-commit-convention
description: Use when committing changes with git — covers Conventional Commits message format and Co-Authored-By signature (harness/version/model/email) across Claude Code and Codex harnesses
---

# Git Commit 规范

## Overview
执行 `git commit` 前调用本 skill，生成 Conventional Commits 规范的 message 和带三要素（harness/版本/模型/邮箱）的 Co-Authored-By 签名。三要素在**同一会话内固定**，首次获取后缓存到上下文，后续 commit 直接复用，不重复执行获取命令。

## When to Use
- 用户要求 commit / 提交 / 你准备执行 `git commit` 时
- 生成或修改 commit message 时

不适用：仅查看 git status / log / diff（不 commit 不触发）。

## 首次执行：识别 harness + 获取三要素（会话内只做一次）

1. **识别 harness**（看系统提示）：
   - 含 "You are Claude Code" → harness = `Claude Code`，版本命令 `claude --version`
   - 含 "Codex" → harness = `Codex`，版本命令 `codex --version`
   - 识别不出 → 默认 `Claude Code`，并提示用户确认
2. **版本**：执行 `{harness-cli} --version`，取版本号（如 `2.1.197`）。失败 fallback `0.0.0`
3. **模型**：读系统提示 "You are powered by the model X" 中的 X（如 `aliyun/glm-5.2`）。读不到 fallback `unknown-model`
4. **邮箱**：执行 `git config user.email`（与 harness 无关）。为空 fallback `noreply@anthropic.com`

**缓存**：以上四元组（harness / 版本 / 模型 / 邮箱）记入上下文。本会话后续 commit **直接复用**，跳过本节。仅当上下文被总结、早期值不可见时重查（值不变，自愈）。

## 每次 commit 都做

### 1. 暂存目标文件
只 `git add` 本次涉及的文件，勿 `git add -A`（避免带入无关改动）。

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

正文用 bullet 列关键改动。**正文不得出现 `@` 符号前导**（避免 PowerShell here-string 残留）。

### 3. 拼 Co-Authored-By 签名
```
Co-Authored-By: {harness}/{version} {model} <{email}>
```
示例：`Co-Authored-By: Claude Code/2.1.197 aliyun/glm-5.2 <wujinxing@sf-express.com>`

### 4. 提交（bash 环境用 heredoc）
```bash
git add <目标文件> && git commit -F - <<'EOF'
<type>: <中文 subject>

- 改动1
- 改动2

Co-Authored-By: {harness}/{version} {model} <{email}>
EOF
```

## Checklist
- [ ] 三要素已获取（本会话首次）或复用（已缓存），未重复执行获取命令
- [ ] subject 中文、`<type>: <subject>` 格式
- [ ] 正文无 `@` 前导
- [ ] 签名四元组齐全、格式正确
- [ ] 只暂存目标文件

## Common Mistakes
| 错误 | 修正 |
|------|------|
| 每次 commit 都重跑 `claude --version` | 会话内只查一次，后续复用上下文已缓存值 |
| `git add -A` 带入无关文件 | 只 add 目标文件 |
| 正文残留 `@`（PowerShell here-string） | 用 `git commit -F -` + heredoc |
| 忘记查邮箱 | 首次必查，为空用 fallback |
| Codex 环境误用 `claude --version` | 先识别 harness 再选版本命令 |
