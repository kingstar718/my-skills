# lbs-cloud（SF 内部框架）服务测试与本地启动

适用：依赖 `com.sf.lbs.cloud.*`（lbs-cloud 3.8.x、Spring Boot 2.7、Nacos、Retrofit）的代理服务，典型为 `gis-rss-ips-*` 高德代理族（place-around / place-around-pro / place-text / place-text-pro / tip-gd 等）。

## 一、本地启动（验证/冒烟）

- 前提：内网可访问 Nacos（`bootstrap.yml` 的 `server-addr`/namespace/group），应用启动时自动拉取 `urlConfig.properties`、`httpPool.properties`、`ds.yml` 等配置。
- 前置：先执行 `mvn -pl <web> -am package -Dmaven.test.skip=true`。注意 `mvn -pl <core> -am test` 只产出 core/api 的 `target/classes`，不构建 web，也不会生成 `target/lib` 与部署 zip（`maven-dependency-plugin` 的 `copy-dependencies` 绑定在 `prepare-package` 阶段）；本地起服务必须以 web 的 package 产物为基础。
- 产物启动（推荐，可复现）：上述 package 产出 `*-web-<env>-<color>.zip`（内含 `lib/<app>.jar` 与全部依赖 jar）。解压后启动：
  ```bash
  C:\software\jdk8\bin\java.exe -Dspring.cloud.nacos.discovery.register-enabled=false -jar lib/<app>.jar
  ```
  端口与 context path（如 `/placearound`）由 Nacos 的 `application-tomcat.yml` 决定；`dev/blue` 包通常没有 `conf/` 目录属正常（conf 仅 prod/uat 需要）。
- 等价形态：IDE 直接运行 web 模块主类（如 `...web.Application`），classpath = 各模块 `target/classes` + `target/lib/*`（同样要求 web 已完成 package），行为与产物启动一致。
- 注册中心：本地调试加 `-Dspring.cloud.nacos.discovery.register-enabled=false`，避免把本地实例注册进测试环境。
- 外部服务调用：应用会走 Nacos 下发的 `httpPool.properties` 代理访问外部服务（如高德）。本地网络不通该代理时典型报 `CONNECT 400`，属环境配置问题而非代码问题；需要真实联调时临时调整 httpPool 代理（直连或可达代理），否则以 SIT e2e 为准。

## 二、分层落地修正

### 1. Tier 1 纯单测优先，逻辑抽 static

可脱离 Spring 验证的逻辑（URL 构建、字符串处理等）优先抽成包级/静态方法（如 `buildPlaceAroundV5Url`），测试零 Spring、秒级。

### 2. graceful-response 静态工厂需要最小上下文

`RestResult.newErr/newSuccess` 与 `Response`/`BaseResponse` 依赖 `ApplicationContextProvider` 等 Spring bean，无法在无上下文时断言。此类测试（infocode 分流、错误映射）在 `core` 使用最小 `TestConfiguration`，不启动 Nacos、不连外部服务：

```java
@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = XxxTest.TestConfig.class)
class XxxTest {
    @TestConfiguration
    static class TestConfig {
        @Bean ApplicationContextProvider applicationContextProvider() { return new ApplicationContextProvider(); }
        @Bean GracefulResponseProperties gracefulResponseProperties() { return new GracefulResponseProperties(); }
        @Bean BaseResponseFactory baseResponseFactory() { return new DefaultBaseRespFactory(); }
        @Bean ResponseFactory responseFactory(BaseResponseFactory b, GracefulResponseProperties p) { return new DefaultRespFactory(b, p); }
        @Bean UrlConfig urlConfig() { /* mock 配置对象，stub getXxxUrl/getXxxAk */ }
        @Bean XxxRemote remote() { return mock(XxxRemote.class); }
    }
}
```

要点：
- 放 `core/src/test/java/.../service/impl/`（镜像被测类），不是 `web` 切片；`web` 仍只放 `@WebMvcTest`。
- 服务类经构造注入 mock 的 `UrlConfig` 与 Retrofit Remote，remote 打桩返回 JSON 响应，断言外层 `status` 与 `result.err/msg`。
- 这类测试的定位是“Tier 1.5”：不连 Nacos/Redis/外部服务，只起最小 Spring 上下文。

### 3. core 测试基建

- `spring-boot-starter-test`（test scope），log4j2 项目排除 `log4j-to-slf4j`、`logback-classic`、`logback-core`（或按仓库现状排除 starter-logging）。
- 显式 `maven-surefire-plugin` 2.22.1（默认 2.12 不识别 JUnit5，测试静默不跑）。
- 本地仓库与构建：JDK8（`JAVA_HOME=C:\software\jdk8`）、`-o` 离线、`-pl <module> -am`（api/core 未 install 时必须带 `-am`）。

## 三、高频坑与模板（实测沉淀）

- OkHttp `HttpUrl.Builder.addQueryParameter` 实测：中文/空格按 UTF-8 编码（空格 `%20`），`& = + #` 分别编码 `%26 %3D %2B %23`，`%` 二次编码 `%25`，逗号编码 `%2C`。禁止字符串拼接 URL（`#` 截断、`&` 串参）。
- 高德 `status=0` 分流模式：`20000→5010`、`20001→5011`、限流码集合（10003/10004/10014/10015/10019/10020/10021/10029/10044）→ `4701` + 自定义 msg，其余兜底 `5003`。
- E2E：仓库根 `e2e/test_<svc>.py`（pytest），携带 `X-Sign-Timestamp`/`X-Sign` 签名头；服务不可达时 `skipif` 可见跳过；回归用例保留“部署前红（复现）→ 部署后绿”基线。
- 项目专属细节（环境地址、AK/SK 默认值、模块命名）以各仓库 AGENTS.md 与既有 spec/e2e 文件为准，不写入本技能。
