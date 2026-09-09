# my-skills

个人 AI 编程 Skill 集合，同时支持 Codex、Claude Code 和 ZCode。

## 包含的 Skill

- `env-tool-log`：机器环境快照、工具调用失败日志与教训提炼，执行命令前查规则/失败日志，失败即记录避免重复踩坑；支持 Codex 与 Claude Code（hooks 自动捕获）。
- `git-commit-convention`：提交前检查目标文件，生成中文 Conventional Commits message，并仅在 AI 身份明确时添加联署。
- `cn-writing`：中文技术写作通用规范（标题、行文硬约束、禁用表达清单、结构、数字术语、代码示例、复验），my-blog-build 等写作类 skill 共用。
- `my-blog-build`：mars-blog（CF Pages + R2）写作到发布的完整工作流（内容 API 上传、frontmatter 规范、触发重建，写作部分引用 cn-writing）。
- `my-interview`：交互式面试教练，基于本地 interview-wiki 题库（290+ 算法题解 + 后端八股），练习/模拟面试双模式。
- `my-statusline`：为 Claude Code 配置底部状态栏(模型 | 目录 | git 分支 | 上下文用量进度条 | 5h/7d 订阅用量)，`/my-statusline` 应用。
- `spring-testing`：为 Spring (Boot) 项目设计并落地分层测试（单测 / WebMvc 切片 / Testcontainers 集成 / pytest E2E），含无 Docker 时的降级方案。
- `spec-coding`：Spec Coding（规范驱动开发）需求跟进——单文件 spec（状态/验收标准 EARS/设计要点/任务清单/TDD/回归），测试先行（红→绿）实现。

## Codex 安装

添加此 Git 仓库作为 marketplace：

```bash
codex plugin marketplace add kingstar718/my-skills
```

然后在 Codex 中打开 `/plugins`，从 `my-skills` marketplace 安装插件。安装或更新后请新建会话。

## Claude Code

仓库继续保留 `.claude-plugin/` 清单，并与 Codex 共用 `plugins/my-skills/skills/` 下的 Skill。

## ZCode

技能正文与 ZCode 的 SKILL.md 规范一致，两种安装方式：

**技能直装（本地开发推荐，随仓库工作区即时同步）**：把 `plugins/my-skills/skills/` 下的技能目录链接到 `~/.zcode/skills/`。Windows 用 junction（每个技能一条，撤销用 `rmdir`）：

```powershell
powershell -NoProfile -Command "New-Item -ItemType Junction -Path \"$HOME\.zcode\skills\env-tool-log\" -Target \"D:\projects\my-skills\plugins\my-skills\skills\env-tool-log\""
```

**插件方式**：设置 → 插件管理 → 发现 → `+` → 添加 GitHub 仓库 `kingstar718/my-skills`（ZCode 兼容 `.claude-plugin/` 清单），安装 `my-skills` 插件。

- `my-statusline` 为 Claude Code 专用（依赖 statusLine 与订阅用量数据），ZCode 下不安装。
- `env-tool-log` 自动捕获 hooks（可选）：`python plugins/my-skills/skills/env-tool-log/scripts/install_zcode_hooks.py` 写 `~/.zcode/cli/config.json`（`PostToolUseFailure` 为 ZCode 官方事件直记失败），新建会话生效；`--uninstall` 移除。
