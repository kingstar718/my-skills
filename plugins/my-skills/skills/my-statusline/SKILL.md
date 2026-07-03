---
name: my-statusline
description: Use when the user asks to install, apply, or manage the Claude Code status line (statusLine). Installs a status bar showing model, current directory, git branch, and a context-usage progress bar (e.g. ▓░░░░░░░░░ 23k/1m).
---

# my-statusline

为 Claude Code 配置底部状态栏(statusLine),显示:

```
模型名 | 当前目录 | git 分支 | ▓░░░░░░░░░ 23k/1m
```

各段带颜色:模型青、目录蓝、分支绿、进度条按用量 <70% 绿 / 70-89% 黄 / ≥90% 红。

> 仅适用于 Claude Code。Codex 的 statusline 机制(`~/.codex/config.toml` 的 `customCommand`)不通过 stdin 传 JSON,本 skill 的脚本不适用于 Codex。

## 安装/应用

当用户说「安装 statusline」「应用 my-statusline」「配置状态栏」等时,执行:

1. 把本 skill 目录下的 `statusline.js` 复制到 `~/.claude/statusline.js`(若已存在,覆盖前提示用户)。
2. 确定 node 可执行路径:
   - 先 `which node`(PATH 含 node 时直接用 `node`)。
   - 找不到则用已知路径,如 scoop 的 `D:/software/scoop/apps/nodejs22/current/node`(Windows)或 `/d/software/scoop/apps/nodejs22/current/node`(Git Bash)。
3. 在 `~/.claude/settings.json` 写入或更新 `statusLine` 字段:
   ```json
   "statusLine": {
     "type": "command",
     "command": "<node 路径> ~/.claude/statusline.js"
   }
   ```
   - 路径一律用正斜杠(Git Bash 会把反斜杠当转义吞掉)。
   - 保留 settings.json 其余字段不变,改完确认 JSON 合法。
4. 用模拟输入验证:
   ```bash
   echo '{"model":{"display_name":"test"},"cwd":"<某 git 仓库路径>","context_window":{"total_input_tokens":23000,"context_window_size":1000000}}' | <node 路径> ~/.claude/statusline.js
   ```
   应输出带颜色的状态栏一行。
5. 告知用户:下次交互后状态栏刷新生效。

## 卸载

从 `~/.claude/settings.json` 删除 `statusLine` 字段;可选删除 `~/.claude/statusline.js`。

## 字段说明

| 段 | 颜色 | 数据源 |
|---|---|---|
| 模型 | 青 (36) | `model.display_name` |
| 目录 | 蓝 (34) | `cwd` 的 basename |
| 分支 | 绿 (32) | `git rev-parse --abbrev-ref HEAD`,无括号;非 git 仓库省略 |
| 进度条+用量 | 按用量变色 | `context_window.total_input_tokens` / `context_window_size`,10 格,有用量至少 1 格 |

## 自定义

修改 `statusline.js` 的字段/颜色/格数后,重新复制到 `~/.claude/statusline.js` 即可(settings.json 路径不变,无需改配置)。
