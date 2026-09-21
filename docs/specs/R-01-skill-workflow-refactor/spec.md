# Skill 文档工作流重构

- 状态：待回归
- 提出日期：2026-09-21
- 更新时间：2026-09-21
- 登记：[docs/project.md](../../project.md)（R-01）
- 设计：[design.md](design.md)
- 验证：[verification.md](verification.md)

## 背景与范围

现有 `spec-coding` 将状态、需求、设计、任务、TDD 和回归强制放在单文件，容易让中大型需求不断
膨胀；`spring-testing` 又把通用测试原则、特定项目模块结构和 lbs-cloud 个案混在一起。本需求重构
二者的职责和交接格式，并为本仓库建立精简、可持续的文档入口。

范围包括：

- 建立仓库级 `AGENTS.md`、需求登记表和目录式 spec 示例。
- 调整 `spec-coding` 的流程、模板、示例和 UI 元数据。
- 调整 `spring-testing` 的分层决策、基础设施边界和条件性参考资料。
- 对齐 Codex、Claude Code 插件版本并验证插件结构。

不包括：迁移使用这些 skill 的其他仓库文档；自动安装或发布插件；合并两个 skill。

## 验收标准

- AC-1：WHEN 需求规模较小且没有独立设计或多阶段验证，`spec-coding` SHALL 支持单文件核心 spec。
- AC-2：WHEN 需求跨组件、包含独立设计或验证记录持续增长，`spec-coding` SHALL 允许采用
  `spec.md`、`design.md`、`verification.md` 分离的目录式结构，且状态只维护在核心 spec。
- AC-3：WHEN 编写验收标准，系统 SHALL 要求每个 AC 有可追溯的验证覆盖；IF 一个 AC 需要多层测试，
  THEN 不强制它与单个单元测试一一对应。
- AC-4：WHEN Spring 任务需要验证业务协作，`spring-testing` SHALL 允许 mock 外部依赖；WHEN 验证
  SQL、Redis/Lua、消息协议或驱动行为，THEN SHALL 使用足够真实且隔离的基础设施。
- AC-5：WHEN 选择测试位置和环境，`spring-testing` SHALL 优先遵循仓库结构和被验证行为，不把
  `core/web`、真实 Nacos 或 Testcontainers 作为所有项目的硬约束。
- AC-6：WHEN E2E 目标环境不可达，THEN 本地可显式跳过；IF 该环境是 CI 或发布门禁的必备目标，
  THEN 测试 SHALL 失败而不是假绿。
- AC-7：WHEN 普通需求完成，THEN 不要求更新 `AGENTS.md`；只有长期仓库规则或入口变化时才更新。
- AC-8：WHEN 两个 skill 协作，`spec-coding` SHALL 管理 AC 与证据映射，`spring-testing` SHALL 细化
  测试层级和实现方式，二者保持独立触发。
- AC-9：WHEN 完成本次修改，THEN 两个 skill 和插件 manifest SHALL 通过结构校验，Codex 与 Claude
  Code manifest 的基础版本保持一致。

## 关键决策

- 核心 spec 是需求契约的唯一真相源，不等于所有材料必须在同一文件。
- 按信息变化频率拆分：稳定契约放 spec，中期设计放 design，易变执行证据放 verification。
- 两个 skill 不合并，也不建立强制双向依赖；仅约定通用验证映射。
- 版本升级到 `1.10.0`，因为本次修改改变了 skill 的工作方式而非仅修正文案。

## 验证映射

| AC | 风险 / 行为 | 验证层级 | 用例 / 证据 | 基线 | 当前结果 |
| --- | --- | --- | --- | --- | --- |
| AC-1～AC-3、AC-7、AC-8 | 单文件、AC 与单测一一对应及收尾追加 `AGENTS.md` 等硬规则造成文档膨胀 | 静态审查 | `spec-coding` 正文、模板、示例及 [verification.md](verification.md) | 强制单文件、AC 对应单测、收尾更新 `AGENTS.md` | 已改为双模式、分层验证证据，且只把长期规则写入 `AGENTS.md` |
| AC-4～AC-6、AC-8 | 测试层级与模块名、基础设施实现绑定，或 E2E 因环境不可达产生假绿 | 静态审查 | `spring-testing` 正文、按需引用及 [verification.md](verification.md) | 固定 core/web、Redis/MQ 不 mock、环境不可达统一 skip | 已改为按风险分层、隔离基础设施和门禁失败语义 |
| AC-9 | 两端元数据漂移，或 skill / plugin 包结构无效 | 自动校验 | skill / plugin 校验器及 [verification.md](verification.md) | 两端基础版本不一致，未执行本轮结构校验 | 基础版本已统一为 `1.10.0`，结构校验通过；安装回归待执行 |

## 待确认项

无。按评审结论：两个 skill 保持独立，采用轻量交接格式。
