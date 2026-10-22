# lbs-cloud 框架测试补充

仅当项目依赖 `com.sf.lbs.cloud.*`，且测试命中产物启动、注册中心、HTTP 代理、graceful-response 静态
上下文或框架日志依赖问题时读取。具体框架版本、模块结构和环境参数以目标仓库为准。

## 本地启动与冒烟

- 先读项目 runbook 和 Maven 绑定。部分 lbs-cloud 多模块项目只在 `package`/`prepare-package` 阶段复制
  依赖并组装部署 zip；`mvn test` 只产生测试和 classes，不能据此假定已有可启动产物。
- 优先使用项目正式 package 产物执行 `java -jar` 冒烟，JDK 路径、profile、主 jar 和解压结构由项目
  决定，不在本参考写死。
- 本地启动连接共享 Nacos/注册中心时，在框架支持的前提下关闭服务注册，只拉取必要配置，避免本地实例
  被测试流量发现；具体属性名以项目使用的 Spring Cloud/Nacos 版本为准。
- 外部 HTTP 调用可能受到配置中心下发的连接池或代理设置影响。出现代理握手、`CONNECT` 或路由错误时，
  先核对本机到代理的可达性和实际下发配置，再判断是否为业务代码问题；不要在测试代码中写死绕过代理。

## 纯逻辑优先

可脱离 Spring 验证的解析、映射和判断逻辑优先放在无状态方法或明确职责的对象中，用纯单测覆盖。不要
仅为测试把领域逻辑改成 static；是否使用实例方法遵循现有设计和注入方式。

## graceful-response 静态工厂

`RestResult.newErr/newSuccess` 内部走 `ApplicationContextProvider.getBean(...)`（该类 `implements ApplicationContextAware`，静态持有容器），无上下文即抛错，无法纯单测。需要断言响应组装时，在被测模块启动只包含响应工厂和桩依赖的最小上下文，不加载配置中心、中间件或 Web 服务：

```java
@ExtendWith(SpringExtension.class)
@ContextConfiguration(classes = XxxInfocodeTest.TestConfig.class)
class XxxResponseTest {
    @Autowired XxxDependency dependency;
    @Autowired XxxServiceImpl service;

    @Test
    void dependencyFailureIsMappedToExpectedResponse() {
        when(dependency.call()).thenReturn(failureResult());
        Response resp = (Response) service.xxx(new XxxReq());
        assertEquals(Integer.valueOf(1), resp.getStatus());
        BaseResponse base = (BaseResponse) resp.getResult();
        assertEquals(EXPECTED_ERROR, base.getErr());
    }

    @TestConfiguration
    static class TestConfig {
        // Aware 回调注入静态容器，RestResult 静态工厂从此可用
        @Bean ApplicationContextProvider applicationContextProvider() { return new ApplicationContextProvider(); }
        @Bean GracefulResponseProperties gracefulResponseProperties() { return new GracefulResponseProperties(); }
        @Bean BaseResponseFactory baseResponseFactory() { return new DefaultBaseRespFactory(); }
        @Bean ResponseFactory responseFactory(BaseResponseFactory b, GracefulResponseProperties p) { return new DefaultRespFactory(b, p); }
        @Bean XxxDependency dependency() { return mock(XxxDependency.class); }
        @Bean XxxServiceImpl service(XxxDependency d) { return new XxxServiceImpl(d); }
    }
}
```

要点：
- 测试放在被测代码所属模块并镜像包结构，不因启动了最小上下文就机械移动到 Web 模块。
- 响应字段和成功/失败 envelope 先根据项目实际框架版本确认，不把示例值当成跨版本契约。
- 无请求线程时 `DefaultRespFactory.getHttpRequest()` 走容错分支不报错，无需模拟 `RequestContextHolder`。
- 最小上下文只补响应组装与框架交互，业务分支仍优先用纯单测验证。

## 测试基建

- `spring-boot-starter-test`（test scope），log4j2 项目排除 `log4j-to-slf4j`、`logback-classic`、`logback-core`（或按仓库现状排除 starter-logging）。
- 使用 JUnit 5 时确认 Surefire/测试引擎版本实际运行用例，不能以 `BUILD SUCCESS` 替代测试计数。
- JDK 绝对路径、Maven profile、模块名、装配包结构、Nacos 地址和完整启动命令属于项目 runbook，不写入
  本参考。
- 业务错误码、供应商协议、鉴权头和环境地址属于项目契约或测试代码，不沉淀为 lbs-cloud 通用规则。
