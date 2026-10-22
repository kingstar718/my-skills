# Testcontainers 集成测试（Tier 3）

## 依赖与版本

```xml
<!-- test scope -->
org.testcontainers:mysql
org.testcontainers:junit-jupiter
```

优先使用项目 BOM 或依赖管理中的兼容版本；新增版本前核对项目 Java、Spring Boot、Docker API 和现有
测试依赖，不在通用模板固定版本。

## 骨架

```java
@Testcontainers
@SpringBootTest(classes = TestApp.class, properties = {
    "spring.sql.init.mode=always",
    "spring.sql.init.schema-locations=classpath:schema-test.sql"
})
@Transactional
class XxxServiceIT {

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.0")
            .withDatabaseName("test").withUsername("t").withPassword("t");

    @Container
    static final GenericContainer<?> REDIS = new GenericContainer<>("redis:7-alpine")
            .withExposedPorts(6379);

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", MYSQL::getJdbcUrl);
        r.add("spring.datasource.username", MYSQL::getUsername);
        r.add("spring.datasource.password", MYSQL::getPassword);
    }
}
```

## Redis/中间件 bean 覆盖

生产客户端可能从外部配置源读取连接信息，集成测试应显式改为隔离实例：

- 测试类内嵌 `@TestConfiguration` 或动态属性，使生产客户端连接隔离实例；
- 优先通过动态属性调整连接；只有确实需要用同名测试 Bean 替换生产 Bean 时，才设置
  `spring.main.allow-bean-definition-overriding=true`；
- 需要同名覆盖时，不要依赖后置“排除器”（BeanDefinitionRegistryPostProcessor）：Bean 重名冲突可能
  在排除器运行前就抛出 `BeanDefinitionOverrideException`。

## Schema 与数据隔离

- 测试建表脚本与生产 DDL 对齐（唯一键、索引、约束都保留），仅去掉实例相关的 `AUTO_INCREMENT` 起始值；
- DB 靠 `@Transactional` 测试结束回滚；Redis 不在事务内，用 `try/finally` 删 key；
- 测试数据统一加唯一前缀并在 `finally`/生命周期钩子中清理。

## 容器不能表达目标拓扑时

单容器不能证明 Redis Cluster 跨槽、双 cell、真实网络路由或厂商中间件行为。此时使用显式参数启用的
隔离环境测试，并满足：默认未配置时清晰跳过；目标地址不得自动指向生产；只操作随机前缀；失败也执行
best-effort 清理；在 CI 门禁中需要该环境时，不得把不可达当作通过。

## 常见坑

- H2/HSQLDB 方言差异（`NOT NULL DEFAULT`、索引、分页）→ 用真实容器；
- 远程 Docker 时容器映射端口必须在测试机可达（见 docker-host-options.md）；
- 生产 `@SpringBootApplication` 扫到测试 classpath 的 `@TestConfiguration` 时，使用显式测试启动类或
  仓库已有隔离方式，避免无关 Bean 进入上下文。
