# my-skills

个人 AI 编程 Skill 集合，同时支持 Codex 和 Claude Code。

## 包含的 Skill

- `env-tool-log`：机器环境快照、工具调用失败日志与教训提炼，执行命令前查规则/失败日志，失败即记录避免重复踩坑；支持 Codex 与 Claude Code（hooks 自动捕获）。
- `git-commit-convention`：提交前检查目标文件，生成中文 Conventional Commits message，并仅在 AI 身份明确时添加联署。
- `my-blog-build`：mars-blog（CF Pages + R2）写作到发布的完整工作流（内容 API 上传、frontmatter 规范、触发重建）。
- `my-interview`：交互式面试教练，基于本地 interview-wiki 题库（290+ 算法题解 + 后端八股），练习/模拟面试双模式。
- `my-statusline`：为 Claude Code 配置底部状态栏(模型 | 目录 | git 分支 | 上下文用量进度条 | 5h/7d 订阅用量)，`/my-statusline` 应用。
- `spring-testing`：为 Spring (Boot) 项目设计并落地分层测试（单测 / WebMvc 切片 / Testcontainers 集成 / pytest E2E），含无 Docker 时的降级方案。

## Codex 安装

添加此 Git 仓库作为 marketplace：

```bash
codex plugin marketplace add kingstar718/my-skills
```

然后在 Codex 中打开 `/plugins`，从 `my-skills` marketplace 安装插件。安装或更新后请新建会话。

## Claude Code

仓库继续保留 `.claude-plugin/` 清单，并与 Codex 共用 `plugins/my-skills/skills/` 下的 Skill。
