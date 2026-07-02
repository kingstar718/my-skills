# my-skills

个人 AI 编程 Skill 集合，同时支持 Codex 和 Claude Code。

## 包含的 Skill

- `git-commit-convention`：提交前检查目标文件，生成中文 Conventional Commits message，并仅在 AI 身份明确时添加联署。

## Codex 安装

添加此 Git 仓库作为 marketplace：

```bash
codex plugin marketplace add kingstar718/my-skills
```

然后在 Codex 中打开 `/plugins`，从 `my-skills` marketplace 安装插件。安装或更新后请新建会话。

## Claude Code

仓库继续保留 `.claude-plugin/` 清单，并与 Codex 共用 `plugins/my-skills/skills/` 下的 Skill。
