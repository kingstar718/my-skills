# R-02 本地随记发布

随记与博客入口的当前名称见[需求(R-07)](R-07-skill-naming.md)；本文保留原实施与验证依据，配置和发布行为继续有效。

状态：已上线。源码、本地测试、Codex 技能发现及生产随记发布均已验证。

## 范围

新增 `my-note-publish` skill、Python 标准库发布脚本及离线接口测试，接入 my-skills 插件。
支持首次配置、保存草稿、预览、发布记录复用、冲突检查和保存后读回验证。
更新 my-blog-build 随记入口及中文写作资源链接，技能界面名称统一为英文标识。
本需求上线时，Codex、Claude Code manifest 和 Claude marketplace 的基础版本统一为 1.11.3。
不修改博客服务端，不增加 MCP，不上传图片，不自动修改或删除已发布内容。

关联需求：

- 与[需求(R-01)](R-01-skill-workflow-refactor.md)共享 cn-writing，发布行为仍按本文验收标准执行。
- [需求(R-03)](R-03-pi-package.md)后续将清单基础版本统一为1.12.0，替代本文范围中的1.11.3版本记录；
  不替代正文发布、凭据或重试规则。本文的历史验证证据仍对应本需求上线时的版本。

## 验收标准与验证

| AC | 行为 | 当前验证结果 |
| --- | --- | --- |
| AC-1 | 从 UTF-8 正文生成无标题随记，时间转 UTC，支持草稿，拒绝空正文、超限及非法 ID | 离线测试通过 |
| AC-2 | 发布读取环境变量或本机配置中的凭据，预览不联网，不回显密码，不跟随重定向 | 离线测试通过 |
| AC-3 | 同名同内容重试不重复 PUT，同名异内容拒绝覆盖 | 离线模拟 HTTP 测试通过 |
| AC-4 | PUT 后 GET 校验原文，区分保存、未知保存结果、读回失败和重建触发结果 | 离线测试通过；生产返回 saved_verified、deployTriggered=true |
| AC-5 | skill 元数据有效、资源链接存在、插件安装包含新 skill | quick_validate 通过；安装文件与源码一致，新 Codex app-server 发现 enabled=true |
| AC-6 | 首次缺少配置时引导 setup，保存后可复用，Windows 加密，取消不保存，环境变量优先 | 离线测试通过；用户实际完成窗口配置并成功发布 |

## 关键决策

正文先生成包含 ID、Markdown 和 SHA-256 的本地发布记录，再联网；重试复用记录。
凭据优先读取 `BLOG_BASE_URL`、`BLOG_ADMIN_PASSWORD`，缺少的项读取本机配置，无环境地址默认值。
默认配置位置为用户目录 `~/.config/my-note-publish/config.json`，可由 `BLOG_NOTE_CONFIG` 覆盖。
Windows 密码使用当前用户 DPAPI 加密，其他平台使用权限 0600 的本机文件；配置和密码不进入仓库。
Windows 支持掩码输入窗口，其他平台在交互终端隐藏输入密码。
GET 预检不提供并发原子写入保障，同一 ID 不应并发发布；脚本不会等待静态页面构建完成。
显式发送 `User-Agent: mars-blog-note-publisher/1.0`，避免生产入口拒绝 Python 默认请求标识。

## 验证证据

Python 3.12：`python -m unittest discover -s <skill>/scripts -p 'test_*.py' -v`，最终源码 16 个测试通过。
模拟接口测试只访问 127.0.0.1，覆盖配置、DPAPI 往返、保存、重试、冲突、鉴权、重定向及读回失败。
Windows 窗口脚本语法校验通过，真实配置窗口已由用户填写并成功保存。
修改过的五个技能均通过 `skill-creator/scripts/quick_validate.py`，JSON/YAML 和资源链接校验通过。
plugin-creator 及其更新脚本在当前环境缺失，使用新基础版本和 Codex CLI 本地安装，未直接修改缓存。
新 app-server 已验证技能可发现且启用，客户端内的配置在下次脚本调用时立即生效。
生产发布保存后原文读回一致、重建触发成功；随后随记页面返回 200，并匹配用户提供的随记正文。
Claude Code 和 pi 尚未执行客户端端到端发布测试。
待确认项：无阻塞项。
