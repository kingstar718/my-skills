# WebMvc 切片测试（Tier 2）

## 骨架

```java
package com.example.app.slice;   // 独立包，避免探测到生产启动类

@WebMvcTest(value = XxxController.class, properties = {
    "spring.cloud.nacos.discovery.enabled=false",
    "spring.cloud.nacos.config.enabled=false",
    "spring.cloud.bootstrap.enabled=false"
})
class XxxControllerTest {
    @Autowired MockMvc mockMvc;
    @MockBean XxxManager manager;
    // 用例：GET/POST 参数绑定、JSON body、header 覆盖逻辑、响应透传
}
```

## 独立启动类（关键坑）

- 切片测试会自动探测 `@SpringBootConfiguration`：如果生产 `Application` 和测试启动类同包，会歧义报错；
- 生产 `Application` 的 `@ComponentScan` 会扫到测试 classpath 上的 `@TestConfiguration`/配置类，导致 Bean 冲突——`excludeFilters` 不生效（冲突发生在扫描阶段）；
- 解法：新建独立切片启动类，**放在不与生产启动类同包/同祖先包的包**（例如 `...slice`），内容为：
  ```java
  @SpringBootConfiguration
  @EnableAutoConfiguration
  @Import(XxxController.class)
  public class SliceTestApp {}
  ```
- 控制器必须 `@Import` 注册：切片扫描以测试所在包为基准，Controller 不在该包时扫不到会 404。

## 用例注释规范

- 类级 Javadoc：说明测试类覆盖范围（映射/绑定/header/响应结构等）与桩掉的对象；
- 每个用例在 `@Test` **之前**写一行 Javadoc：场景 + 预期结果（如“GET 缺 q 返回 400，manager 不被调用”）。

## 响应工厂依赖 Spring 上下文（graceful-response 等）

- `RestResult.newXxx()` 内部经 `ApplicationContextProvider` 从 Spring 容器取 `ResponseFactory` Bean，纯 JVM/单测调用会 NPE；`@WebMvcTest` 也只加载 web 自动配置，不会带业务自动配置；
- 解法：在独立 `SliceTestApp` 中手工注册所需 Bean，例如：
  ```java
  @Bean public GracefulResponseProperties gracefulResponseProperties() { return new GracefulResponseProperties(); }
  @Bean public BaseResponseFactory baseResponseFactory() { return new DefaultBaseRespFactory(); }
  @Bean public ResponseFactory responseFactory(BaseResponseFactory b, GracefulResponseProperties p) { return new DefaultRespFactory(b, p); }
  @Bean public ApplicationContextProvider applicationContextProvider() { return new ApplicationContextProvider(); }
  ```
- 不要 mock `Response` 接口代替：Jackson 会序列化 Mockito 内部字段（`mockitoInterceptor`）导致序列化报错；
- 若响应工厂被 `@MockBean` 的 manager 桩掉，校验/映射等纯逻辑应收敛为可单测方法，避免依赖容器。

## 日志依赖排除（log4j2 项目）

- `spring-boot-starter-test` 传递引入 `log4j-to-slf4j` 与 logback，与项目 log4j2（`log4j-slf4j-impl`）冲突：前者抛 `LoggingException`，后者在 Spring 启动时报 `LoggerFactory is not a Logback LoggerContext`；
- 在 starter-test 依赖上排除 `org.apache.logging.log4j:log4j-to-slf4j`、`ch.qos.logback:logback-classic`、`ch.qos.logback:logback-core`（test scope 内生效，不影响生产）。

## 适用范围

- URL 映射、GET/POST 参数绑定、请求头处理、响应 JSON 结构；
- 不需要 DB/Redis/配置中心，秒级，CI 常驻。
