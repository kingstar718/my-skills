# AGENTS.md

## 仓库定位

本仓库维护可同时供 Codex、Claude Code 和 ZCode 使用的个人技能。插件源码位于
`plugins/my-skills/`；安装目录和 `~/.codex/plugins/cache/` 仅是生成或缓存结果，不是修改入口。

## 修改入口

- Skill 源码：`plugins/my-skills/skills/<skill-name>/`
- Codex manifest：`plugins/my-skills/.codex-plugin/plugin.json`
- Claude Code manifest：`.claude-plugin/plugin.json`
- Marketplace：`.agents/plugins/marketplace.json`
- 需求登记：`docs/project.md`
- 中大型需求：`docs/specs/<R-xx-name>/`

不要直接修改 Codex 插件缓存。发布时保持 Codex 与 Claude Code manifest 的基础版本一致；Codex
本地迭代所需的 cachebuster 通过插件更新脚本生成，不手改 marketplace。

## 文档工作流

- 小改动可在一份核心 spec 中完成；跨 skill、包含独立设计或多阶段验证的需求使用目录式 spec。
- 核心 spec 只维护状态、范围、验收标准、关键决策和验证映射，是需求契约的唯一真相源。
- 详细设计写 `design.md`，执行证据写 `verification.md`；不在多个文件复制相同正文。
- `AGENTS.md` 只放长期有效的仓库约束和入口；Git 历史承担修订历史。

## Skill 约定

- `SKILL.md` 保留触发条件、核心决策和资源路由；条件性细节放 `references/`。
- `assets/` 是生成产物使用的模板，不作为默认加载的完整说明书。
- 描述要能准确区分适用任务，避免把项目特例提升为通用规则。
- 修改 `SKILL.md` 时同步检查 `agents/openai.yaml`，默认提示必须显式提到 `$skill-name`。
- 不为单个项目写死模块名、机器路径、环境地址、凭据、错误码或依赖版本。

## 验证

修改 skill 时运行当前环境 `skill-creator` 自带的 `quick_validate.py`；修改插件结构或 manifest 时，
同时运行 `plugin-creator` 自带的 `validate_plugin.py`。Windows 读取中文 UTF-8 文件若受默认 GBK 编码影响，
先设置 `PYTHONUTF8=1`。

同时检查 JSON/YAML 可解析、相对链接存在，以及两个 manifest 的基础版本一致。需要让 Codex
加载本地改动时，按 plugin-creator 的 cachebuster + reinstall 流程操作，并在新会话验证。
