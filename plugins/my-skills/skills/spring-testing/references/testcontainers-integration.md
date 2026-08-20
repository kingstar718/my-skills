# Testcontainers 集成测试（Tier 3）

## 依赖（web 模块 pom）

```xml
<testcontainers.version>1.20.4</testcontainers.version>
<!-- test scope -->
org.testcontainers:mysql
org.testcontainers:junit-jupiter
```

版本兼容：Spring Boot 2.x/Java 8 用 1.20.x；Boot 3.x 可用 1.20+/2.x。

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

## Redis/中间件 bean 覆盖（关键坑）

生产 Redis bean 的构造器通常直接读配置中心（Nacos），测试要指向容器：

- 测试类内嵌 `@TestConfiguration` 提供同名 bean（如 `geoProWhiteRedisPrd`），用 Lettuce 直连容器；
- 测试属性加 `spring.main.allow-bean-definition-overriding=true`；
- 不要依赖"排除器"（BeanDefinitionRegistryPostProcessor）：Bean 重名冲突发生在排除器运行之前，会直接抛 `BeanDefinitionOverrideException`。

## Schema 与数据隔离

- 测试建表脚本与生产 DDL 对齐（唯一键、索引、约束都保留），仅去掉实例相关的 `AUTO_INCREMENT` 起始值；
- DB 靠 `@Transactional` 测试结束回滚；Redis 不在事务内，用 `try/finally` 删 key；
- 测试数据统一加前缀（如 `__test_`）防撞真实数据。

## 常见坑

- H2/HSQLDB 方言差异（`NOT NULL DEFAULT`、索引、分页）→ 用真实容器；
- 远程 Docker 时容器映射端口必须在测试机可达（见 docker-host-options.md）；
- 生产 `@SpringBootApplication` 会扫到测试 classpath 的 `@TestConfiguration` → 集成测试用显式 `classes=TestApp`，测试启动类放到不与生产启动类同包的子包并改 public。
