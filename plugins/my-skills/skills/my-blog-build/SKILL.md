---
name: my-blog-build
description: 为 mars-blog（Cloudflare Pages + R2 静态站）生成/修改文章与随记并发布的完整工作流：通过内容 API 上传 markdown 到 R2、触发重建上线。当用户要求写新文章、修改现有文章、发短文/随记、构建博客或发布内容时使用。
---

# my-blog-build

面向 mars-blog（v3，Cloudflare Pages 静态化）的端到端写作与发布方案。覆盖内容规范、内容 API 上传、重建等待与校验全流程。

## 项目与内容真相源

```text
~/projects/mars-blog/    # 源码仓库（astro + Pages Functions，本机在 /root/projects/mars-blog）
```

**内容真相源是 R2（CONTENT 桶）里的 markdown，不是 git 仓库。** 仓库里只有代码和一个 `about.md` 占位页；线上内容的发布一律走内容 API（或浏览器登录后就地编辑），git push 只用于改代码。

发布链路：`PUT /api/content/...` → 写 R2 → 触发 Deploy Hook → Pages 重新构建（`sync-content` 拉最新 markdown 到 `src/content/` 后 `astro build`）→ 新内容约 1-2 分钟上线。

## 一、内容规范

### 内容目录（R2 前缀 = API 路径）

```text
posts/   # 正式文章（有标题，进时间线，slug = 文件名）
notes/   # 短文/随记（无标题，正文一两段，直接在时间线展开）
pages/   # 固定页（目前只有 about.md，title 可选）
```

### Frontmatter Schema（以 `src/content.config.ts` 的 Zod schema 为准，多余的键会被丢弃）

**posts/（文章）**

```yaml
---
title: 文章标题               # 必填，non-empty
description: 一句话摘要        # 可选，默认 ""
pubDatetime: "2026-08-25T10:30:00.000Z"   # 必填，ISO8601 UTC，见下
featured: false              # 可选
canonical_url: https://...   # 可选（注意是 snake_case）
draft: false                 # 可选；true = 草稿，构建跳过
updated: "2026-08-25T11:00:00.000Z"  # 可选，保存时自动写
---
```

**notes/（短文）**——只有两个字段，**没有 title**：

```yaml
---
pubDatetime: "2026-08-25T10:30:00.000Z"
draft: false
---
```

**pages/（固定页）**——只有 `title`（可选）。

**`pubDatetime` 格式 = ISO8601 UTC**（编辑器产自 `new Date().toISOString()`，如 `2026-08-25T10:30:00.000Z`）。显示时自动转站点时区 Asia/Shanghai。**不要写无偏移的 `YYYY-MM-DD HH:mm`**：`z.coerce.date()` 会把无偏移字符串当 UTC 解析，展示会差 8 小时。

**已经从旧站 schema 移除、不要再写的字段**：`updates`、`aiGenerated`、`author`、`tags`、`modDatetime`、`timezone`。旧站的「更新记录 / AI 角标」机制在 mars-blog 里不存在；内容修改靠 `updated` 字段或直接改正文。

### 写作规范

**正文写作一律遵守通用写作 skill [`cn-writing`](../../cn-writing/SKILL.md)——动笔前先读取该文件，再开始写作。** 其中「标题、行文硬约束、禁用表达清单、结构约束、数字与术语、代码与示例、复验清单」全部适用。

下文只列站点特有的内容约定；frontmatter 见上方「Frontmatter Schema」。

### Markdown 写作约定（站点特有）

- **标题层级**：正文从 `##` 开始，层级不超过 `####`
- **链接**：站内文章用相对路径 `[标题](/posts/slug)`；外部链接 `[文字](https://...)`
- **图片**：正文引用 `/media/<key>`，不写本地路径
- **中文排版**：中英文之间加空格；中文语句用全角标点
- **文件名 = slug**：小写英文 + 连字符（`my-post.md`）；中文标题交给 `title`，不进文件名。新文章编辑器产出的 slug 形如 `2026-08-25-1752000000000.md`（UTC 日期-毫秒时间戳）

## 二、发布——内容 API（主路径，脚本/快捷指令/外部工具）

### 鉴权（二选一）

- `Authorization: Bearer <ADMIN_PASSWORD>`：脚本最省事。`ADMIN_PASSWORD` 是 CF Pages 的加密变量（登录口令）
- 登录 cookie：先 `POST /api/auth/login`（表单字段 `password`）拿会话 cookie 带上；浏览器端就地编辑走的就是这条

### 端点

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/content` | 列出全部内容 |
| GET | `/api/content/posts` | 列出某目录（notes/pages 同理） |
| GET | `/api/content/posts/<slug>.md` | 读取 markdown 原文 |
| PUT | `/api/content/posts/<slug>.md` | 上传长文（覆盖写） |
| PUT | `/api/content/notes/<slug>.md` | 上传短文（随记） |
| DELETE | `/api/content/posts/<slug>.md` | 删除 |

限制：只允许 `posts|notes|pages` 前缀下的 `.md` 且防 `..` 逃逸；单文件 ≤ 1MB；登录接口同 IP 十分钟限 10 次。**全部端点（含 GET）都要鉴权**：未带凭证统一 401。

### 上传长文

```bash
# frontmatter + 正文组织成完整 markdown 后整体 PUT
curl -X PUT https://<你的域名>/api/content/posts/我的文章.md \
  -H "Authorization: Bearer $ADMIN_PASSWORD" \
  --data-binary "---
title: 我的文章
pubDatetime: \"$(date -u +%Y-%m-%dT%H:%M:%S.000Z)\"
description: 一句话摘要
---

正文……
"
```

### 上传短文（随记）

```bash
curl -X PUT https://<你的域名>/api/content/notes/2026-08-25-1752000000000.md \
  -H "Authorization: Bearer $ADMIN_PASSWORD" \
  --data-binary $'---\npubDatetime: "2026-08-25T10:30:00.000Z"\n---\n\n一两段正文。'
```

### 草稿 / 修改 / 删除

- **草稿**：frontmatter 里带 `draft: true`，构建会跳过，页面不出现；发布时**删掉 `draft` 字段**再 PUT
- **修改**：先 `GET` 读回原文保留其余字段，只改标题/正文/`updated`，再 PUT 覆盖
- **删除**：`DELETE` 同路径，同样触发重建

### 图片

- 浏览器端上传：压缩成多尺寸后 `POST /api/admin/images`（FormData：`file` + `meta` JSON），写入 MEDIA 桶
- 正文中引用 `/media/<key>` 相对路径，由 `functions/media/[[path]].ts` 代理出图；**不要引用本地文件路径**

### 上线确认

PUT 返回 `{"ok":true}` 后轮询：`GET /api/content/posts/<slug>.md` 能读到新内容、页面能访问，即完成（约 1-2 分钟，Deploy Hook 触发重建）。

## 三、发布——浏览器就地编辑（备路径）

登录 `https://<你的域名>/login` 后：文章页点铅笔原地变编辑态、短文在列表就地展开、`/new-post` 是空白稿纸。保存 = 走同一套 content API（标题 + `pubDatetime` 进 frontmatter，`updated` 自动更新，发布时去掉 `draft`），随后页面轮询到重建完成自动刷新。**适合人工微调，脚本批量操作直接用上一节的 API。**

## 四、构建与校验

- **CI（强制）**：push 到 main / 开 PR 时 GitHub CI 跑 `format:check` + `build`（含 `astro check`）——但注意 **CI 只校验代码，不校验线上内容**；内容 schema 校验发生在 Pages 构建时（`astro build` 校验 frontmatter，写错会构建失败、内容不上线）
- **本地构建**（可选）：`cd ~/projects/mars-blog && pnpm build`。本地 `src/content/` 只有占位内容，构建只验证代码与 schema；要看真实内容，先配 R2 凭据跑 `pnpm sync:content`
- **Functions 类型检查**：`pnpm typecheck:functions`
- 常见失败：frontmatter 有多余字段（schema 外键会被丢弃但别依赖）、`title` 缺失（短文才有 title-free 的 schema）、`pubDatetime` 非 ISO 日期、正文超过 1MB

## 五、发布前检查清单

- [ ] 目录正确：文章 → `posts/`，短文 → `notes/`，固定页 → `pages/`
- [ ] frontmatter 只含当前 schema 字段（无 `updates`/`aiGenerated`/`author`/`tags`；`canonical_url` 是下划线）
- [ ] `pubDatetime` 是 ISO8601 UTC（带 `Z`），不用无偏移时间
- [ ] 短文没有 `title`；文章 `title` 必填、`description` 一句话
- [ ] 要发布的**不带** `draft: true`（草稿=带 draft，发布=删掉该字段）
- [ ] `updated` 已在修改时更新
- [ ] 图片引用用 `/media/...`，不是本地路径
- [ ] 已按 `cn-writing` 复验清单逐项检查（标题/禁用表达/数字术语/代码示例）
- [ ] PUT 后 GET 读回确认内容、等待重建完成、页面可访问