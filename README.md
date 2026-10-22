# my-skills

个人 AI 编程 Skill 集合，同时支持 Pi、Codex、Claude Code 和 ZCode。

## 包含的 Skill

- `env-tool-log`：共享 shell 与内置工具经验索引，同类错误原位更新，修复后保留预防规则；支持 Codex 与可选 Claude Code/ZCode hooks。
- `git-commit-convention`：提交前检查目标文件，生成中文 Conventional Commits message，并仅在 AI 身份明确时添加联署。
- `cn-writing`：中文技术写作通用规范（标题、行文硬约束、禁用表达清单、结构、数字术语、代码示例、复验），my-blog-build 等写作类 skill 共用。
- `my-blog-build`：mars-blog（CF Pages + R2）写作到发布的完整工作流（内容 API 上传、frontmatter 规范、触发重建，写作部分引用 cn-writing）。
- `my-note-publish`：从本地正文文件发布无标题随记或存草稿，生成可复用发布记录、检查同名冲突并读回验证；使用博客内容 API，无需 Memos 或 R2 凭据。
- `my-interview`：交互式面试教练，基于本地 interview-wiki 题库（290+ 算法题解 + 后端八股），练习/模拟面试双模式。
- `my-statusline`：为 Claude Code 配置底部状态栏(模型 | 目录 | git 分支 | 上下文用量进度条 | 5h/7d 订阅用量)，`/my-statusline` 应用。
- `spring-testing`：按风险为 Spring (Boot) 项目选择并落地单测、切片、真实基础设施集成与黑盒 E2E，明确 mock、Testcontainers 和隔离环境的边界。
- `spec-coding`：以核心 spec、可测 AC 和验证证据跟进需求；小需求保持单文件，复杂需求按需拆分设计与验证产物。

## Codex 安装

添加此 Git 仓库作为 marketplace：

```bash
codex plugin marketplace add kingstar718/my-skills
```

然后在 Codex 中打开 `/plugins`，从 `my-skills` marketplace 安装插件。安装或更新后请新建会话。

## Claude Code

仓库继续保留 `.claude-plugin/` 清单，并与 Codex 共用 `plugins/my-skills/skills/` 下的 Skill。

## Pi

仓库根 `package.json` 提供 Pi 包清单，`pi.skills` 指向 `plugins/my-skills/skills`：

```bash
# 其他机器：从 GitHub 安装
pi install git:github.com/kingstar718/my-skills

# 本仓库开发：按路径就地加载，随工作区改动即时同步
pi install D:\projects\my-skills

# 只试用一次，不写入配置
pi -e D:\projects\my-skills
```

安装或更新后 `/reload` 或新建会话生效。清单里 `my-statusline` 以排除项（`-` 前缀）去掉，Pi 下加载 8 个 Skill。

## ZCode

技能正文与 ZCode 的 SKILL.md 规范一致，两种安装方式：

**技能直装（本地开发推荐，随仓库工作区即时同步）**：把 `plugins/my-skills/skills/` 下的技能目录链接到 `~/.zcode/skills/`。Windows 用 junction（每个技能一条，撤销用 `rmdir`）：

```powershell
powershell -NoProfile -Command "New-Item -ItemType Junction -Path \"$HOME\.zcode\skills\env-tool-log\" -Target \"D:\projects\my-skills\plugins\my-skills\skills\env-tool-log\""
```

**插件方式**：设置 → 插件管理 → 发现 → `+` → 添加 GitHub 仓库 `kingstar718/my-skills`（ZCode 兼容 `.claude-plugin/` 清单），安装 `my-skills` 插件。

- `my-statusline` 为 Claude Code 专用（依赖 statusLine 与订阅用量数据），ZCode 下不安装。
- `env-tool-log` 自动捕获 hooks（可选）：`python plugins/my-skills/skills/env-tool-log/scripts/install_zcode_hooks.py` 写 `~/.zcode/cli/config.json`（`PostToolUseFailure` 为 ZCode 官方事件直记失败），新建会话生效；`--uninstall` 移除。
