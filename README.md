# my-skills

供 Codex、Claude Code 和 Pi 使用的个人 Skill 集合，
涵盖需求开发、测试、Git 提交、内容编写、博客发布、交互学习与工具经验复用。
`claude-statusline` 仅适用于 Claude Code。

## 包含的 Skill

- [`code-spec`](plugins/my-skills/skills/code-spec/SKILL.md)：澄清代码需求、核对业务术语，
  按需调研、原型与拆任务，默认在单份需求 Markdown 中维护规则和验收证据。
- [`code-test`](plugins/my-skills/skills/code-test/SKILL.md)：按行为和风险选择跨技术栈测试，
  建立复现、诊断故障并回归；Spring 分层与基础设施经验按需读取。
- [`code-review`](plugins/my-skills/skills/code-review/SKILL.md)：分别审查代码质量与需求符合度，
  核对验证证据和影响范围，按需进行工程复盘或代码任务交接。
- [`git-commit`](plugins/my-skills/skills/git-commit/SKILL.md)：检查提交范围，
  生成中文 Conventional Commits 提交说明，仅在用户授权时暂存和提交。
- [`env-tool-log`](plugins/my-skills/skills/env-tool-log/SKILL.md)：复用 shell 与内置工具的经验，
  同类错误原位更新，修复后保留预防规则。
- [`content-write`](plugins/my-skills/skills/content-write/SKILL.md)：规范文章、说明、文案等文本的表达、结构与语义，按语言和格式应用排版规则；
  编写 Agent 文档时按需检查引用触发、完成条件和信息层级。
- [`blog-publish`](plugins/my-skills/skills/blog-publish/SKILL.md)：为 mars-blog 编写或修改内容，
  通过内容 API 上传并触发 Cloudflare Pages 构建。
- [`blog-note-publish`](plugins/my-skills/skills/blog-note-publish/SKILL.md)：通过博客内容 API 发布无标题随记或保存草稿，
  复用发布记录并读回验证。
- [`interview`](plugins/my-skills/skills/interview/SKILL.md)：基于本地 interview-wiki 题库练习算法与后端八股，
  支持练习和模拟面试，复用已有档案记录掌握证据并安排复习。
- [`learn`](plugins/my-skills/skills/learn/SKILL.md)：研究新知识并连接已有概念，
  生成 HTML 交互课程，依据真实练习表现调整难度、补齐短板并跨会话续学。
- [`claude-statusline`](plugins/my-skills/skills/claude-statusline/SKILL.md)：配置 Claude Code 底部状态栏，
  显示模型、目录、Git 分支、上下文用量与订阅用量。

## 统一安装与更新

使用 [skills CLI](https://github.com/vercel-labs/skills) 为多个客户端安装同一套技能。
需要 Node.js 22.20 或更高版本；其他机器也可直接运行以下命令，无需手动克隆仓库或创建目录联接。

### 安装

为 Codex、Pi 和 Claude Code 全局安装通用技能：

```bash
npx skills add kingstar718/my-skills -g -a codex -a pi -a claude-code
```

在交互界面选择除 `claude-statusline` 外的10个技能，并选择链接安装(Symlink)。
安装器维护共享内容与客户端入口：Codex、Pi 读取 `~/.agents/skills/`，
Claude Code 通过 `~/.claude/skills/` 中的链接读取。

Claude Code 的状态栏技能单独安装：

```bash
npx skills add kingstar718/my-skills -g -a claude-code --skill claude-statusline
```

安装后新建会话，Pi 也可执行 `/reload`。
从下方客户端安装方式切换时，移除或停用原有 my-skills 加载入口，避免重复加载。

### 检查与更新

```bash
npx skills list -g
npx skills check
npx skills update -g
```

以上依次列出全局技能、检查可用更新、更新全局技能。
更新命令会处理该安装器管理的全部全局技能，不限于本仓库；
原有插件市场或 Pi 包安装的副本仍由各自安装方式维护。
完整选项见 [skills CLI 命令说明](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)。

### 从旧技能名称迁移

发布包含改名的版本后，按下表迁移；源码不保留旧技能的兼容副本。

| 旧名称 | 当前名称 |
| --- | --- |
| `git-commit-convention` | `git-commit` |
| `my-blog-build` | `blog-publish` |
| `my-note-publish` | `blog-note-publish` |
| `my-interview` | `interview` |
| `my-learn` | `learn` |
| `my-statusline` | `claude-statusline` |
| `cn-writing` | `content-write` |

先安装并检查新入口，再移除已安装的旧名称：

```bash
npx skills add kingstar718/my-skills -g -a codex -a pi -a claude-code --skill git-commit blog-publish blog-note-publish interview learn content-write
npx skills list -g
```

原来使用状态栏技能的 Claude Code 用户另装专用入口：

```bash
npx skills add kingstar718/my-skills -g -a claude-code --skill claude-statusline
```

确认对应新入口存在后，按名称移除旧技能副本：

```bash
npx skills remove git-commit-convention my-blog-build my-note-publish my-interview my-learn my-statusline cn-writing -g
```

更早的 `spec-coding`、`spring-testing` 已分别改为 `code-spec`、`code-test`，另新增 `code-review`。
仍在使用旧代码技能时，同样先安装新入口再移除旧名称：

```bash
npx skills add kingstar718/my-skills -g -a codex -a pi -a claude-code --skill code-spec code-test code-review
npx skills remove spec-coding spring-testing -g
```

只选择实际使用的客户端和技能。改名或新增入口需显式安装，不能只依赖 `skills update`。
插件或 Pi 包用户沿用原更新方式，并检查旧入口是否移除；迁移后新建会话，Pi 也可 `/reload`。
仓库外指令、调用命令和配置中显式引用旧名称的地方需同步修改。

改名只涉及技能入口，不迁移个人数据。随记配置继续使用
`~/.config/my-note-publish/config.json`，面试 Cookie 和内容库缓存继续使用 `~/.my-interview/`。
已有学习档案、发布记录、环境变量、env-tool-log 数据及 `~/.claude/statusline.js` 的位置均不变。
旧规格中的名称用于追溯，当前映射见[需求(R-07)](docs/R-07-skill-naming.md)。

### 学习方式

调用示例：

```text
使用 $learn 帮我学习线程池，目标是能解释积压并选择合适的队列策略。
```

课程与个人档案保存在学习工作区，不在技能安装目录。
HTML 支持本地实验和作答导出；将结果文件交给 Agent 后，它才能分析表现、安排下一课。
此方式不要求模型后端，网页本身不会持续生成新题或自动同步学习进度。

## 客户端安装方式(可选)

以下方式与统一安装二选一，也可用于客户端专用安装或本地开发。

### Codex

添加仓库作为插件市场：

```bash
codex plugin marketplace add kingstar718/my-skills
```

在 Codex 中打开 `/plugins`，从 `my-skills` 市场安装同名插件。
安装或更新后新建会话。

### Claude Code

在 Claude Code 会话中依次添加市场、打开插件安装界面：

```text
/plugin marketplace add kingstar718/my-skills
/plugin install my-skills@my-skills
```

选择安装范围并完成安装，按客户端提示加载插件。
命令与安装范围见 [Claude Code 官方安装说明](https://code.claude.com/docs/en/discover-plugins)。

### Pi

从 GitHub 安装：

```bash
pi install git:github.com/kingstar718/my-skills
```

本地开发时，在仓库根目录按路径加载；单次试用使用 `-e`：

```bash
pi install .
pi -e .
```

安装或更新后执行 `/reload` 或新建会话。
`package.json` 排除 Claude Code 专用的 `claude-statusline`，Pi 加载其余10个 Skill。

## 工具经验复用

`env-tool-log` 默认使用 `~/.my-skills/env-tool-log/` 保存本机数据，
可通过 `ENV_TOOL_LOG_DIR` 指定其他目录。
同一用户的各客户端应使用同一目录；快照、日志与经验不随插件分发。

安装 Skill 不会自动把经验注入新会话。
在各客户端支持的全局指令入口加入以下约定：

> 会话首次使用 shell 或内置工具时，读取共享 env-tool-log 经验索引的相关章节；
> 已读取且环境未变化时复用。同类错误原位更新，修复验证后关闭记录并保留预防规则。

Claude Code 另提供可选 hooks，用于自动捕获错误和提示经验。
安装插件不会自动启用这些 hooks；接入与旧目录迁移见
[数据与使用说明](plugins/my-skills/skills/env-tool-log/references/data-and-usage.md)。
