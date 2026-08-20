---
name: spring-testing
description: "Design and implement layered tests for Spring (Boot) projects: pure unit tests in core modules, WebMvc slice tests, SpringBootTest integration tests with Testcontainers for real MySQL/Redis, and black-box HTTP E2E with pytest. Use when asked to write, organize, migrate, or review tests for a Spring project; choose between H2/Testcontainers/mocks; run Spring integration tests without local Docker; set up Testcontainers, slice-test isolation, or pytest E2E test suites."
---

# Spring 项目测试

为 Spring（Boot）项目设计并落地分层测试。按"必须真 vs 可以桩"决策外部依赖，按模块放测试，避免内存库方言陷阱。

## 测试分层与落点

| 层 | 位置 | 覆盖 | 外部依赖 |
|----|------|------|----------|
| Tier 1 纯单测 | `core/src/test/java/...`（按被测包镜像） | service/manager/config/工具逻辑 | 无，秒级 |
| Tier 2 切片 | `web/src/test/java/.../slice/` | `@WebMvcTest` Controller 层（映射/绑定/header/序列化） | 无 |
| Tier 3 集成 | `web/src/test/java/.../` | `@SpringBootTest` + Testcontainers（真实 DB/Redis + 配置源） | Docker + 可达配置中心 |
| E2E | 仓库根 `e2e/`（pytest，独立于 Maven） | 黑盒打真实网关（部署后行为） | 可达测试环境 |

规则：
- 只有需要 Spring 上下文的测试放 `web`；纯逻辑单测放 `core`；`api` 模块不写业务单测（契约测试预留）。
- E2E 不参与 Maven `-P test`，CI 单独 stage。

## 基础设施选择

- **数据库**：Testcontainers 真实 MySQL，不用 H2/HSQLDB（方言差异会制造假阳性）。
- **Redis/MQ**：Testcontainers 容器（真实行为），不 mock。
- **配置中心（Nacos 等）**：是来源不是行为——可达就真实连，否则 `@MockBean`/本地配置桩掉。
- **无 Docker**：按顺序降级——远程 Docker 主机（VirtualBox VM）→ 嵌入式二进制（MariaDB4j/embedded-redis）→ 纯 mock。详见 [docker-host-options.md](references/docker-host-options.md)。

## 落地流程（按需读引用）

1. 盘点外部依赖，按上表分类，确定分层。
2. 写 Tier 1 单测：纯 JUnit5 + Mockito，不启动 Spring。
3. 写 Tier 2 切片：`@WebMvcTest` + 独立启动类。见 [slice-tests.md](references/slice-tests.md)。
4. 写 Tier 3 集成：Testcontainers 容器 + 动态属性注入 + bean 覆盖。见 [testcontainers-integration.md](references/testcontainers-integration.md)。
5. 写 E2E：单文件 pytest 黑盒。见 [e2e-pytest.md](references/e2e-pytest.md)。

## 验收标准

- 单测/切片秒级、零外部依赖；集成测试 schema 与生产 DDL 对齐；E2E 环境不可达时可见跳过（不静默假绿）。
- 新增测试遵守既有分层；不改动生产代码逻辑只为测试服务。
