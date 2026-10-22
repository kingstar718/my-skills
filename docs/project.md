# 需求登记

| 编号 | 需求 | 涉及范围 | 关联需求 | 状态 | 规格 |
| --- | --- | --- | --- | --- | --- |
| 需求(R-01) | 研发文档职责、渐进审阅及中文写作规范 | spec-coding、spring-testing、cn-writing | 与[需求(R-02)](R-02-local-note-publish.md)共享写作规范，沿用[需求(R-03)](R-03-pi-package.md)的接入规则并升级清单版本；技能名称与扩展范围由[需求(R-05)](R-05-skill-capability-consolidation.md)承接 | 待回归 | [规格](R-01-skill-workflow-refactor.md) |
| 需求(R-02) | 本地随记发布 skill 与确定性脚本 | my-note-publish、my-blog-build、发布脚本及插件接入 | 与[需求(R-01)](R-01-skill-workflow-refactor.md)共享写作规范；清单版本后由[需求(R-03)](R-03-pi-package.md)替代 | 已上线 | [规格](R-02-local-note-publish.md) |
| 需求(R-03) | Pi 包清单与安装说明 | Pi manifest、客户端清单版本及安装文档 | 扩展[需求(R-02)](R-02-local-note-publish.md)沿用的插件结构，替代其清单版本记录；版本后由[需求(R-01)](R-01-skill-workflow-refactor.md)升级 | 已上线 | [规格](R-03-pi-package.md) |
| 需求(R-04) | 工具失败日志检索与闭环 | env-tool-log 规则、脚本及 UI 元数据 | 沿用[需求(R-01)](R-01-skill-workflow-refactor.md)的单份规格与验证约定，无行为替代关系 | 待回归 | [规格](R-04-env-tool-log.md) |
| 需求(R-05) | 技能能力升级与收敛 | cn-writing、code-spec、code-test、code-review、my-interview 及迁移引用 | 扩展[需求(R-01)](R-01-skill-workflow-refactor.md)，沿用[需求(R-04)](R-04-env-tool-log.md)的工具经验闭环及[需求(R-03)](R-03-pi-package.md)的接入约定 | 待回归 | [规格](R-05-skill-capability-consolidation.md) |
