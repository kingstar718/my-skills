# 命令与接口

所有相对脚本路径均相对于本 skill 目录，实际调用时使用该目录下脚本的绝对路径。

## 配置与使用

首次发布没有配置时，skill 会引导打开本地窗口输入域名和密码。也可以手动运行：

```powershell
python scripts/publish_note.py setup --gui
```

`--gui` 仅适用于 Windows。其他系统在自己的终端运行 `python scripts/publish_note.py setup`，
密码隐藏输入；非交互终端不接受密码输入，也不退化成明文输入。
域名可以填 `blog.example.com`，自动补 `https://`。密码是博客的 `ADMIN_PASSWORD`。

配置保存在用户目录 `~/.config/my-note-publish/config.json`，不进入 Git 仓库。
技能入口改名为 `blog-note-publish` 后仍沿用该路径，环境变量和发布记录格式不变。
Windows 密码由 DPAPI 加密，只有当前 Windows 用户可以解密；其他系统保存在权限 0600 的本机文件。
再次运行 `setup` 可替换配置；取消窗口不保存、不发布。配置不会检查线上密码是否正确，发布时由 API 鉴权。
配置完成后无需重启 Codex，脚本每次运行都会读取本机配置。

已有 `BLOG_BASE_URL`、`BLOG_ADMIN_PASSWORD` 环境变量时仍可使用，两项分别优先于本机配置。
`BLOG_NOTE_CONFIG` 可指定其他配置文件位置，供多站点或测试使用。
脚本不读取 `.env`，不改用户的永久环境变量；环境变量由启动 Codex 的进程继承。

先准备，再发布；重试继续使用 `note-prepared.json`：

```powershell
python scripts/publish_note.py prepare --file body.md --out note-prepared.json
python scripts/publish_note.py publish --prepared note-prepared.json --dry-run
python scripts/publish_note.py publish --prepared note-prepared.json
```

`prepare` 的输入是 Markdown 正文，不是带 frontmatter 的完整文章。它保留正文，只添加随记元数据。
发布记录不能覆盖已有文件，包含生成的 ID、Markdown 及 SHA-256，不含凭据。
`--id` 可指定小写字母、数字和连字符组成的 ID；默认使用 UTC 日期和 UUID。
`--pub-datetime` 接受带偏移的 ISO8601 时间，并转成 UTC；`--draft` 添加 `draft: true`。
`publish --timeout` 设置每次 HTTP 请求超时秒数，默认 30，范围 1–120。

## 服务端契约

- `GET /api/content/notes/<id>.md`：返回 Markdown 原文；不存在时 404。
- `PUT /api/content/notes/<id>.md`：请求体为完整 UTF-8 Markdown。
- 鉴权：`Authorization: Bearer <ADMIN_PASSWORD>`，读取也需要鉴权。
- 保存响应：`{"ok": true, "deployTriggered": true或false}`。
- 单文件上限：1,000,000 个 UTF-8 字节。随记只有 `pubDatetime` 和可选的 `draft` 元数据，没有 `title`。

仅允许 HTTPS 博客地址；本地模拟测试允许 `http://localhost`、`http://127.0.0.1` 或 `http://[::1]`。
地址不能包含用户名密码、查询参数、片段或路径。禁止跟随 HTTP 重定向，避免凭据被转发。

## 输出与重试

非交互命令向 stdout 输出一行 JSON；`setup` 的终端模式另有输入提示，GUI 模式只输出配置状态。
成功退出码为 0，失败为 1，CLI 参数错误为 2。配置结果不包含密码。
准备和预览不会发送网络请求。发布前检查远端同名内容，PUT 后再次 GET 核对完整原文。
结果包含 `key`、`apiUrl`（联网时）、`status`、`saved`、`verified` 和 `deployTriggered`（能判断时）。
`deployTriggered` 为 `null` 表示无法判断，不能解释为失败或成功。

同名同内容的检查用于顺序重试，不提供服务端原子写入保障；不要并发发布同一个 ID。
脚本不会等待静态页面构建完成；内容 API 读回只能证明 R2 内容，不能证明页面上线。
若需要确认公开展示，另行检查静态页面中对应的新内容，不能仅凭 `/notes` 返回 200 判断。
