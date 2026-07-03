#!/usr/bin/env node
// Claude Code 底部状态栏(statusLine)
// 由 my-statusline skill 安装到 ~/.claude/statusline.js
// 从 stdin 读取 Claude Code 会话 JSON,输出:模型 | 目录 | git 分支 | 上下文用量进度条
// 纯 node 内置模块 + git CLI,Win/Linux/Mac 三端通用。

const fs = require("fs");
const { execSync } = require("child_process");

const d = JSON.parse(fs.readFileSync(0, "utf8"));
const ESC = String.fromCharCode(27);
const color = (code) => ESC + "[" + code + "m";
const reset = color(0);

const parts = [];

// 模型名(青色 36)
parts.push(color(36) + (d.model?.display_name || "") + reset);

// 当前目录名(蓝色 34);split 同时匹配 \ 和 /,三端通用,不依赖平台 path 分隔符
parts.push(color(34) + (d.cwd || "").split(/[\\/]/).filter(Boolean).pop() + reset);

// git 分支(绿色 32,无括号;不在 git 仓库则省略)
let branch = "";
try {
  branch = execSync("git --no-optional-locks rev-parse --abbrev-ref HEAD", {
    cwd: d.cwd,
    stdio: ["pipe", "pipe", "ignore"],
  }).toString().trim();
} catch (e) {}
if (branch) parts.push(color(32) + branch + reset);

// 上下文用量:10 格进度条 + 已用/总量(k/m 简写),按已用比例变色
const used = d.context_window?.total_input_tokens || 0;
const size = d.context_window?.context_window_size || 1000000;
const pct = Math.min(100, Math.floor((used / size) * 100));
const fmt = (n) =>
  n < 1000 ? "" + n
  : n < 1000000 ? Math.round(n / 1000) + "k"
  : (Math.round(n / 1000000 * 10) / 10) + "m";
const fill = Math.min(10, Math.ceil((used / size) * 10)); // 有用量至少 1 格,0 用量全空
const col = pct < 70 ? 32 : pct < 90 ? 33 : 31;           // <70% 绿 / 70-89% 黄 / >=90% 红
parts.push(
  color(col) +
    "▓".repeat(fill) + "░".repeat(10 - fill) +
    " " + fmt(used) + "/" + fmt(size) +
    reset
);

process.stdout.write(parts.join(" | "));
