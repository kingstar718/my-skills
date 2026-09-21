---
name: spring-testing
description: "Design, implement, organize, or review layered tests for Spring (Boot) projects. Select the lowest-cost layer that proves the behavior; decide when mocks, slices, real infrastructure, Testcontainers, isolated clusters, or black-box E2E are appropriate. Do not use for generic requirement tracking or non-Spring test suites."
---

# Spring 项目测试

为 Spring（Boot）项目设计并落地分层测试。先识别要证明的行为和风险，再选择足够真实且成本最低的
测试层级。测试位置遵循仓库结构，不用模块名代替测试语义。

## 测试分层与落点

| 层 | 证明什么 | Spring/外部依赖 |
|----|----------|-----------------|
| Tier 1 纯单测 | 纯计算、领域规则、协作与失败分支 | 不启动 Spring；依赖用 stub/mock |
| Tier 2 切片 | MVC 映射、参数绑定、序列化、局部组件装配 | 只启动目标切片；其余依赖桩掉 |
| Tier 3 集成 | Bean 装配、事务、SQL/Redis/MQ/驱动或协议语义 | 最小必要上下文 + 隔离的真实基础设施 |
| E2E | 已部署系统的跨进程 HTTP 契约与关键用户路径 | 黑盒访问明确的测试目标 |

规则：
- 优先沿用仓库已有模块、命名、测试插件和 CI 分层；只有缺少约定时才提出新结构。
- 测试层级由启动范围和依赖真实性定义，不由 `core`、`web`、`api` 等目录名定义。
- 先选能证明风险的最低层级；不要用 E2E 覆盖所有分支，也不要用 mock 声称证明了中间件行为。
- 若已有需求 spec，将测试层级、用例位置和外部依赖回填到 AC 验证映射；本 skill 不管理需求状态。

## 基础设施选择

- **业务协作**：验证调用条件、参数、返回值和异常分支时，mock 数据库、Redis、MQ 或远程服务。
- **基础设施语义**：验证 SQL 方言/事务/锁、Redis Lua/TTL、消息序列化或客户端行为时，使用与生产语义
  相符的隔离实例；Testcontainers 是常见选择，不是唯一选择。
- **拓扑行为**：Cluster、双 cell、网络或厂商中间件无法由单容器表达时，使用显式指定的隔离环境；
  测试必须使用唯一前缀并清理数据，禁止自动写入生产或共享业务数据。
- **配置中心**：默认用测试属性或配置桩。只有配置加载、group/namespace 隔离或热更新本身是目标时，
  才连接真实配置中心。
- **无 Docker**：根据目标在远程容器、嵌入式服务、隔离环境和纯 mock 之间选择，记录没有覆盖的风险。
  详见 [docker-host-options.md](references/docker-host-options.md)。

## 落地流程（按需读引用）

1. 盘点要证明的行为、失败模式和现有测试结构。
2. 从 Tier 1 开始，只有当前层无法证明风险时才上移。
3. MVC 切片的隔离与上下文陷阱见 [slice-tests.md](references/slice-tests.md)。
4. 真实数据库/Redis 等集成方式见 [testcontainers-integration.md](references/testcontainers-integration.md)。
5. 黑盒 HTTP 测试和环境门禁见 [e2e-pytest.md](references/e2e-pytest.md)。
6. 仅当项目依赖 `com.sf.lbs.cloud.*` 且命中对应问题时，读取
   [lbs-cloud-service-test.md](references/lbs-cloud-service-test.md)。

## 工程约定

- 测试应默认可由标准测试命令执行；不要在模块配置里永久跳过测试。若流水线已经在前置阶段完成验证，
  后续纯打包阶段可按仓库约定跳过重复执行，并明确该依赖关系。
- Maven 使用 JUnit 5 时，Surefire 至少为 2.22；具体版本优先跟随项目 BOM，并确认测试实际运行且数量
  不为 0，不能只看构建成功。Gradle 同样要确认测试引擎实际识别用例。
- Testcontainers、数据库和中间件版本优先跟随项目 BOM 与生产兼容范围，不在通用 skill 固定最新版本。
- 用例命名和注释遵循仓库风格；描述应能从失败输出看出场景与预期，不强制所有项目使用同一种注释格式。
- 不修改生产可见性或引入无业务价值的包装只为方便测试；可以通过合理职责拆分提升可测试性。

## 验收标准

- 单测/切片应快速、确定且不依赖共享环境；集成测试保留被验证的生产约束并隔离数据。
- 本地可选 E2E 在环境不可达时可以显式跳过；CI/SIT/发布门禁声明目标环境必备时必须失败。
- 最终报告说明每个风险由哪一层证明、哪些外部行为仍未覆盖，避免“BUILD SUCCESS 但没有测试运行”。
