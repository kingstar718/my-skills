# R-03 Pi 包清单

状态：已上线。清单解析、技能集合、资源加载与 Git 源端到端安装均已验证。

## 范围

在仓库根新增 `package.json`，以 `pi` 键声明 Pi 包清单，`pi.skills` 指向 `plugins/my-skills/skills`，
并用 `-` 排除项去掉 Claude Code 专用的 `my-statusline`。
README 增加 Pi 安装章节，AGENTS.md 登记 Pi manifest 入口与校验要求。
本需求上线时，Codex manifest、Claude Code manifest、Claude marketplace 与 Pi 清单的基础版本统一为1.12.0。
不修改任何 skill 正文，不改动 Codex、Claude Code、ZCode 的既有安装方式，不新增运行时依赖。

关联需求：

- 扩展[需求(R-02)](R-02-local-note-publish.md)沿用的插件目录及接入方式，新增 Pi 包入口。
- 本文的1.12.0清单版本替代需求(R-02)范围中的1.11.3记录，发布脚本业务规则保持独立。
- [需求(R-01)](R-01-skill-workflow-refactor.md)后续将各清单基础版本统一到2.0.0，
  替代本文的版本约定；Pi技能选择规则及历史验证证据保持原适用范围。

## 验收标准与验证

| AC | 行为 | 当前验证结果 |
| --- | --- | --- |
| AC-1 | Pi 按清单解析出 8 个技能，且不含 `my-statusline` | 本地源与 Git 源均解析出 8 个技能，`my-statusline` 未加载 |
| AC-2 | 按包加载时技能元数据有效、无诊断 | 用 Pi 资源加载器加载该包，8 个技能全部有效，diagnostics 为 0 |
| AC-3 | 既有客户端的发现结果不变 | 两个既有 manifest 与 Claude marketplace 仅版本号变化，路径与技能列表未变 |
| AC-4 | 文档覆盖安装方式与排除说明，各清单版本一致 | README 已加 Pi 章节；四处版本统一为 1.12.0，JSON 均可解析 |

## 关键决策

用仓库根 `package.json` 而不是把技能挪到仓库根 `skills/`，避免破坏 Codex 插件目录结构与既有安装。
`pi.skills` 用“目录 + 排除项”而不是逐个列举技能目录，新增技能无需改清单。
排除项写成 `-./plugins/my-skills/skills/my-statusline`：Pi 对 `!` 模式的匹配不做 `./` 归一化
（`!./path` 不命中），`-` 精确排除会归一化，因此选用 `-`。
Pi 清单与 Codex、Claude Code manifest、Claude marketplace 的基础版本保持同步，沿用仓库既有约定。

## 验证证据

Pi 1.2.0：`DefaultPackageManager.resolveExtensionSources(["D:/projects/my-skills"], { temporary: true })`
解析出 8 个 `SKILL.md` 且全部 enabled，`my-statusline` 不在结果中；extensions、prompts、themes 均为 0。
Pi 1.2.0：隔离 agent 目录后以 `packages: ["D:/projects/my-skills"]` 调用 `DefaultResourceLoader.reload()`，
得到 8 个技能、diagnostics 为 0（同一次运行另有 `~/.agents/skills` 的 2 个技能，与本次改动无关）。
Pi 1.2.0：`pi install git:github.com/kingstar718/my-skills` 克隆提交 `752c9bc` 到 agent 目录后，
按全局 `packages` 加载得到同一组 8 个技能、diagnostics 为 0，`my-statusline` 未加载。
9 个技能均通过 `skill-creator/scripts/quick_validate.py`；四处清单 JSON 解析通过且版本号一致。
待确认项：无阻塞项。
