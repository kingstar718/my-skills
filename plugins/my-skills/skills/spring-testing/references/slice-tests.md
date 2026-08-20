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

## 适用范围

- URL 映射、GET/POST 参数绑定、请求头处理、响应 JSON 结构；
- 不需要 DB/Redis/配置中心，秒级，CI 常驻。
