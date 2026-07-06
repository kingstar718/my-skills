---
name: my-statusline
description: Use when the user asks to install, apply, or manage the Claude Code status line (statusLine). Installs a status bar showing model, current directory, git branch, and a context-usage progress bar (e.g. ▓░░░░░░░░░ 23k/1m).
---

# my-statusline

为 Claude Code 配置底部状态栏(statusLine),显示:

```
模型名 | 当前目录 | git 分支 | ▓░░░░░░░░░ 23k/1m | 5h 24% 12:34 | 7d 41% 7/11 10:24
```

各段带颜色:模型青、目录蓝、分支绿、进度条与 5h/7d 用量均按百分比 <70% 绿 / 70-89% 黄 / ≥90% 红。`5h`(5 小时窗口)和 `7d`(7 天/周窗口)来自 `rate_limits`,仅对 Claude.ai 订阅者、且本会话首次 API 响应后才出现,缺失时自动省略该段。百分比后跟该窗口的重置时刻(本地时间,当天只显示 `HH:MM`,跨天显示 `M/D HH:MM`);`resets_at` 缺失时省略时刻。

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
   echo '{"model":{"display_name":"test"},"cwd":"<某 git 仓库路径>","context_window":{"total_input_tokens":23000,"context_window_size":1000000},"rate_limits":{"five_hour":{"used_percentage":24},"seven_day":{"used_percentage":41}}}' | <node 路径> ~/.claude/statusline.js
   ```
   应输出带颜色的状态栏一行,末尾含 `5h 24% | 7d 41%`(省略 `rate_limits` 时这两段不显示)。
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
| 5h 用量 | 按用量变色 | `rate_limits.five_hour.used_percentage` + `resets_at` 重置时刻,缺失则省略 |
| 7d 用量 | 按用量变色 | `rate_limits.seven_day.used_percentage`(7 天/周窗口) + `resets_at` 重置时刻,缺失则省略 |

## 自定义

修改 `statusline.js` 的字段/颜色/格数后,重新复制到 `~/.claude/statusline.js` 即可(settings.json 路径不变,无需改配置)。
