# AGENTS.md

## 仓库定位

本仓库维护可同时供 Pi、Codex 和 Claude Code 使用的个人技能。插件源码位于
`plugins/my-skills/`；安装目录和 `~/.codex/plugins/cache/` 仅是生成或缓存结果，不是修改入口。

## 修改入口

- Skill 源码：`plugins/my-skills/skills/<skill-name>/`
- Codex manifest：`plugins/my-skills/.codex-plugin/plugin.json`
- Claude Code manifest：`.claude-plugin/plugin.json`
- Pi manifest：`package.json`（`pi.skills`）
- Marketplace：`.agents/plugins/marketplace.json`
- 需求登记：`docs/project.md`
- 需求正文：默认使用单份 `docs/R-xx-name.md`，已有入口以 `docs/project.md` 为准。

不要直接修改 Codex 插件缓存。发布时保持 Codex manifest、Claude Code manifest、Pi manifest 与 Claude
marketplace 的基础版本一致；Codex 本地迭代所需的 cachebuster 通过插件更新脚本生成，不手改 marketplace。

## 文档工作流

- 默认在单份需求 Markdown 中维护规则、设计要点和验证结果。
- 用户明确要求或部分内容确需独立维护时才拆分；不以篇幅、复杂度或对话轮次决定。
- 核心 spec 只维护状态、范围、验收标准、关键决策和验证映射，是需求契约的唯一真相源。
- 已有独立设计或验证文档时，用链接引用，不在多个文件复制相同正文。
- `AGENTS.md` 只放长期有效的仓库约束和入口；Git 历史承担修订历史。

## Skill 约定

- `SKILL.md` 保留触发条件、核心决策和资源路由；条件性细节放 `references/`。
- `assets/` 是生成产物使用的模板，不作为默认加载的完整说明书。
- 描述要能准确区分适用任务，避免把项目特例提升为通用规则。
- 修改 `SKILL.md` 时同步检查 `agents/openai.yaml`，默认提示必须显式提到 `$skill-name`。
- 不为单个项目写死模块名、机器路径、环境地址、凭据、错误码或依赖版本。

## 版本规则

版本格式为 `A.B.C`，每位均为0~9的单个数字。
本次以 `2.0.0` 为新基线，替代不符合位数要求的历史 `1.12.0`，避免版本回退。

- **常规升级**：默认只将末位 `C` 加1，不按功能规模自行升级中间位。
- **大版本升级**：用户明确要求「大版本」时，才将中间位 `B` 加1并将 `C` 归零。
- **首位与上限**
  - 首位 `A` 仅在用户明确指定或授权重设基线时调整。
  - 某位达到9时不自动进位；无法按规则递增时先明确新版本，不擅自扩大位数。
- **多组件同步**：整体包、Codex、Claude Code 和 Claude marketplace 的基础版本同时更新。
  Pi 沿用整体包版本；没有独立版本字段的技能或清单不新增版本字段。
- **安装缓存**：Codex cachebuster 仍由插件更新脚本生成，不手改 marketplace 或安装缓存。

## 验证

修改 skill 时运行当前环境 `skill-creator` 自带的 `quick_validate.py`；修改插件结构或 manifest 时，
同时运行 `plugin-creator` 自带的 `validate_plugin.py`。Windows 读取中文 UTF-8 文件若受默认 GBK 编码影响，
先设置 `PYTHONUTF8=1`。

同时检查 JSON/YAML 可解析、相对链接存在，以及各客户端 manifest 与 marketplace 的基础版本一致。
Pi 清单改动还需确认解析出的技能集合符合预期（Pi 包清单与设置项都用 `!`/`+`/`-` 前缀做筛选，
其中 `!` 模式的匹配不做 `./` 归一化，路径需写成 `-./path` 或 `!path`）。需要让 Codex
加载本地改动时，按 plugin-creator 的 cachebuster + reinstall 流程操作，并在新会话验证。
