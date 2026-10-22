---
name: blog-note-publish
description: 从本地正文文件发布随记到支持 /api/content/notes 的博客，生成无标题 Markdown、复用发布 ID、上传后读回校验。用于发随记、短文或保存随记草稿；长文与站点构建使用 blog-publish。
---

# 本地发布随记

使用 Python 3.10+，无需安装第三方依赖。内容通过博客内容 API 写入 R2，保存后由服务端触发静态站重建。

## 配置

优先读取 `BLOG_BASE_URL` 和 `BLOG_ADMIN_PASSWORD`，缺少的项从本机配置补齐。
首次发布返回 `missing_config` 时，引导填写博客域名和站点 `ADMIN_PASSWORD`：

- Windows：说明即将打开本地配置窗口，运行 `scripts/publish_note.py setup --gui`。
  窗口同时填写域名和密码，密码掩码显示。工具返回运行中的 session 时继续等待用户操作；
  用户保存后复用原发布记录继续发布，取消时保留正文和记录，不发布，也不循环弹窗。
- 其他系统：提示用户在自己的交互终端运行 `scripts/publish_note.py setup`，域名可见、密码隐藏。
  Agent 的非交互工具不能代填密码，配置完成后再继续发布。

不要求用户在聊天中提交密码，不输出密码，不把密码放进命令参数、正文、发布记录或仓库。
本机配置会跨会话复用；Windows 使用当前用户 DPAPI 加密，其他系统使用权限 0600 的本机文件。
只要求写正文或预览时不启动配置窗口。配置位置、重配和环境变量覆盖见
[references/usage.md](references/usage.md)。

## 发布流程

1. 识别用户是要发布、存草稿还是只写正文。用户已明确要求发布时直接执行；只要求写作时停在准备阶段。
2. 用户提供完整正文时保留原文；需要生成或润色正文时读取同插件的
   [content-write](../content-write/SKILL.md)。随记没有标题，不添加长文的 `#ai` 标题标签。
3. 把正文写入 UTF-8 文件，运行 `scripts/publish_note.py prepare --file <正文文件> --out <发布记录.json>`。
   脚本生成唯一文件名、带偏移的 UTC 发布时间和完整 Markdown；草稿加 `--draft`。
   用户指定时间时用 `--pub-datetime` 传 ISO8601 时间，必须带 `Z` 或明确偏移。
4. 发布前可运行 `scripts/publish_note.py publish --prepared <发布记录.json> --dry-run` 查看内容。
5. 发布时运行 `scripts/publish_note.py publish --prepared <发布记录.json>`，读取 JSON 结果。
   每次重试复用同一个发布记录。脚本先 GET 检查同名文件：内容相同跳过 PUT，内容不同拒绝覆盖。
6. 只报告脚本证明的状态。`saved_verified` 表示 R2 原文读回一致；`deployTriggered: true`
   仅表示重建请求成功，页面通常还需约 1–2 分钟更新。草稿不会公开展示。

不要把本地正文文件当作 R2 的内容真相源。发布记录保留在用户工作目录或临时目录，不能写进插件源码。
正文中的图片应使用已有 `/media/...` 地址；上传图片和修改已发布内容交给 `blog-publish`。

## 失败处理

- `already_saved`：同名同内容已存在，未重复写入或触发重建；这次不能判断上次重建是否成功。
- `missing_config`：按配置流程引导填写缺失项，成功后继续使用原记录。
- `conflict`：同名文件内容不同，检查发布记录和远端内容，不自动覆盖或生成新 ID 重试。
- `save_uncertain`：PUT 结果不确定，使用原发布记录重跑，先读远端再决定是否写入。
- `saved_unverified`：保存接口成功但读回失败或不一致，保留记录并核查，不换 ID 再发。
- `deployTriggered: false`：内容已保存，重建未成功触发。说明需要检查服务端 Deploy Hook；不循环 PUT。
- 鉴权失败、HTTP 错误或超时：按结果说明失败阶段，不回显凭据，不无限重试。

接口范围、命令示例和状态说明见 [references/usage.md](references/usage.md)。
