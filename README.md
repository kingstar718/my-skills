# my-skills

供 Codex、Claude Code 和 Pi 使用的个人 Skill 集合，
涵盖需求开发、测试、Git 提交、中文写作、博客发布与工具经验复用。
`my-statusline` 仅适用于 Claude Code。

## 包含的 Skill

- [`spec-coding`](plugins/my-skills/skills/spec-coding/SKILL.md)：登记需求、定义验收标准并跟进验证。
  默认在单份需求 Markdown 中维护；用户明确要求或部分内容确需独立维护时才拆分。
- [`spring-testing`](plugins/my-skills/skills/spring-testing/SKILL.md)：为 Spring 项目选择并实现单元测试、
  切片测试、基础设施集成测试与端到端测试，按行为和风险选择验证层级。
- [`git-commit-convention`](plugins/my-skills/skills/git-commit-convention/SKILL.md)：检查提交范围，
  生成中文 Conventional Commits 提交说明，仅在用户授权时暂存和提交。
- [`env-tool-log`](plugins/my-skills/skills/env-tool-log/SKILL.md)：复用 shell 与内置工具的经验，
  同类错误原位更新，修复后保留预防规则。
- [`cn-writing`](plugins/my-skills/skills/cn-writing/SKILL.md)：规范中文技术写作的行文、结构、标点与 Markdown 源码换行。
- [`my-blog-build`](plugins/my-skills/skills/my-blog-build/SKILL.md)：为 mars-blog 编写或修改内容，
  通过内容 API 上传并触发 Cloudflare Pages 构建。
- [`my-note-publish`](plugins/my-skills/skills/my-note-publish/SKILL.md)：通过博客内容 API 发布无标题随记或保存草稿，
  复用发布记录并读回验证。
- [`my-interview`](plugins/my-skills/skills/my-interview/SKILL.md)：基于本地 interview-wiki 题库练习算法与后端八股，
  支持练习和模拟面试。
- [`my-statusline`](plugins/my-skills/skills/my-statusline/SKILL.md)：配置 Claude Code 底部状态栏，
  显示模型、目录、Git 分支、上下文用量与订阅用量。

## 安装

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
`package.json` 排除 Claude Code 专用的 `my-statusline`，Pi 加载其余8个 Skill。

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
