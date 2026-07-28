---
name: my-blog-build
description: 为 astro-paper-blog 生成/修改博客文章并完成构建、校验与推送的完整工作流。当用户要求写新文章、修改现有文章、构建博客或发布到 GitHub 时使用。
---

# my-blog-build

面向 astro-paper-blog 个人博客的端到端写作与发布方案。覆盖内容规范、文章生成、构建校验、Git 推送全流程。

## 项目路径

```text
~/Documents/projects/astro-paper-blog/
```

以下所有相对路径均以此为项目根。

## 一、内容规范

### 文章目录

```text
src/content/posts/   # 正式发布的博客文章（.md）
src/content/notes/   # 短文：一两段的碎片记录，在列表里直接展开，无标题、无详情页
src/content/pages/   # 独立页面（about.md 等）
```

### Frontmatter Schema

每篇文章头部必须包含以下 YAML frontmatter，与 `src/content.config.ts` 的 Zod schema 对应：

```yaml
---
pubDatetime: "2026-07-07 20:00"              # 唯一日期字段，必填，必须加引号
title: 文章标题                                # 必填
description: 文章摘要，出现在时间线条目和 RSS 中  # 必填
featured: false                              # 是否精选（可选，默认 false）
draft: false                                 # 草稿不公开（可选）
canonicalURL: https://...                    # 规范链接（可选，通常不填）
---
```

字段以 `src/content.config.ts` 的 Zod schema 为准，schema 里没有的键会被静默丢弃。

**`pubDatetime` 是全站唯一的日期字段**：排序和页面显示都读这一个值，所以两者永远一致。不存在 `modDatetime`。

格式是 `"YYYY-MM-DD HH:mm"`，**按站点时区（Asia/Shanghai）解读，写的就是页面上显示的值**——不要再手算 UTC 偏移。**必须加引号**：不加引号且带秒的写法会被 YAML 直接解析成时间戳，绕过 schema 的时区处理。写错格式时构建会失败并提示正确写法，不会静默出错。

短文（`src/content/notes/`）的 schema 更窄，只有 `pubDatetime`（必填）和 `draft`（可选）——没有 `title`，写了也不会渲染。

**已经移除、不要再写的字段**：`author`（作者统一取 `astro-paper.config.ts` 的 `site.author`）、`modDatetime`、`tags`、`timezone`（时区统一取站点配置 `Asia/Shanghai`）。

### Markdown 写作约定

- **标题层级**：正文从 `##` 开始（`h1` 由 `title` 渲染），层级不超过 `####`
- **链接**：站内文章用相对路径 `[标题](/posts/slug)`；外部链接用 `[文字](https://...)`
- **图片**：放 `src/assets/images/`，文章中用 `![alt](/src/assets/images/xxx.png)` 引用
- **代码块**：必须标记语言 ` ```typescript `，行内代码用单反引
- **中文排版**：中英文之间加空格；中文语句用全角标点
- **日期式章节**（仅「改造日志」这类持续更新的文章）：`##` 是日期本身（`## 2026-07-28`），具体条目用 `###` 作为子标题，按日期倒序排列

### 写作质量要求

每篇文章在生成或修改后，必须逐项自检：

- **简洁**：一句话能说清的不用一段话。删掉"众所周知""值得一提的是""另外还有一点"等冗余引导词。每个段落只承载一个核心信息点。
- **明了**：技术概念首次出现时用一句话解释，不假设读者已掌握。复杂流程用有序列表拆解，不堆砌成段落。
- **流畅**：段落之间逻辑衔接自然，避免跳跃。从"是什么"到"为什么"再到"怎么做"的顺序展开。
- **用词规范**：技术术语保持统一（同一概念通篇用同一个词，不混用同义词）。中文技术词汇参考业界通用译法（如"渲染"不写"绘制"、"构建"不写"编译"）。
- **可读性**：正文段落不超过 5 行（以 80 字符宽度计）。关键操作步骤用有序列表，配配置/代码用代码块。适当使用加粗强调关键结论。
- **复验**：生成后通读一遍，检查是否有主谓不搭配、时态混乱、语序倒错、重复啰嗦等问题。技术描述与实际代码行为是否一致。列表项之间是否存在逻辑交叉或遗漏。

### 文件命名

- 文件名 = 文章 slug，小写英文 + 连字符：`astro-paper-customization-journey.md`
- 中文标题通过 `title` frontmatter 表达，不放在文件名中

## 二、文章生成与修改

### 新建文章

1. 确认 `src/content/posts/` 下没有同名文件
2. 按上述 Frontmatter Schema 填写元数据：
   - `pubDatetime` 取当前北京时间，写成 `"YYYY-MM-DD HH:mm"`（`TZ=Asia/Shanghai date "+%Y-%m-%d %H:%M"`）
   - `draft: false`（如果准备发布）
3. 正文按 Markdown 写作约定组织
4. 在文章末尾追加更新记录块（见「五、AI 生成与更新记录」），记录本次创建操作
5. 写完后本地预览验证

### 修改已有文章

1. 读取目标文章的完整内容，理解现有结构和风格
2. 检查文末是否存在 `<details>` 更新记录块；不存在则新建，存在则在表格首行插入本次记录
3. 修改正文内容
4. **`pubDatetime` 默认不动**——修改的痕迹由文末的更新记录块承载，日期字段保持文章的发布时间。只有在正文有实质重写、确实希望这篇重新回到时间线顶部时才更新它（例如「改造日志」这类持续更新的文章）。改错别字、修失效引用不要动日期，否则老文章会因为一处小修就顶上首页

## 三、构建与校验

### 本地预览

```bash
cd ~/Documents/projects/astro-paper-blog
pnpm dev          # 开发模式，热重载，http://localhost:4321
```

### 构建检查

```bash
pnpm build        # astro check → astro build → pagefind 索引
```

构建成功标准：0 errors / 0 warnings。产物在 `dist/`。

### 常见构建问题

| 症状 | 原因 | 处理 |
|------|------|------|
| `pubDatetime 需要加引号` | YAML 把日期解析成了时间戳 | 给值加双引号，并去掉秒 |
| `pubDatetime 格式应为...` | 用了 ISO 或其他格式 | 改成 `"YYYY-MM-DD HH:mm"`，北京时间 |
| frontmatter 校验失败 | Zod schema 不匹配 | 检查 `title`/`description` 是否齐全、有无多余字段 |
| 日期显示或排序不对 | 忘记更新 `pubDatetime` | 改过正文就要同步更新它，全站只有这一个日期字段 |
| 图片 404 | 路径错误 | 检查图片是否在 `src/assets/images/` 且引用路径正确 |
| pagefind 索引异常 | 搜索内容为空 | 确认文章非 draft 且包含正文 |
| `@import must precede` | CSS 加载顺序 | 确认字体加载在 Layout.astro `<head>` 中，不在全局 CSS 中 |

## 四、发布与推送

### Git 提交流程

1. 在 astro-paper-blog 仓库根目录执行：

```bash
git status                    # 确认改动范围
git add src/content/posts/xxx.md [其他改动文件]
git diff --cached             # 最后确认暂存内容
```

2. Commit message 按 `git-commit-convention` skill 的规范生成，footer 用：

```text
<type>(post): <中文简述>

AI-Generated-By: <Agent 名称及版本> / <模型>
```

`type` 按实际操作选择：`feat`（新文章）、`fix`（修正内容）、`refactor`（结构调整）、`chore`（格式修正）。

3. 文章中必须同步追加更新记录（见第五节），与 commit message 互相对应。

4. 推送：

```bash
git push origin main
```

### 部署

项目无自动部署 workflow（`.github/workflows/ci.yml` 只做 lint、format:check 和 build 校验）。推送后需手动触发部署或使用 Vercel/Railway 等平台的 Git 集成自动部署 `dist/` 目录。

### 发布前检查清单

- [ ] 本地 `pnpm build` 通过（0 errors / 0 warnings）
- [ ] `pnpm dev` 预览文章渲染效果
- [ ] 检查暗色模式下代码块和排版是否正常
- [ ] frontmatter 只含 schema 里有的字段（没有 `author`/`modDatetime`/`tags`/`timezone`）
- [ ] `draft: false`（准备公开发布）
- [ ] 修改文章时 `pubDatetime` 已更新为当前时间
- [ ] commit message 包含 `AI-Generated-By` footer
- [ ] 文末 `<details>` 更新记录块已追加本次操作，`<summary>` 时间已更新
- [ ] 文章已通读复验（语法、逻辑、术语一致性）

## 五、AI 生成与更新记录

每篇由 AI 创建或修改的文章，必须在文末放置一个可见的更新记录区域。使用 HTML `<details>` 元素实现折叠展开：默认只显示最新一条记录，点击展开后显示全部历史，倒序排列（最新的在最上面）。

**不要在记录块前加 `---` 分割线**，直接以引用行开头。

时间格式统一使用 `YYYY-MM-DD HH:mm:ss`（UTC+8，Asia/Shanghai），精确到秒。

### 更新记录块格式

```markdown
> 本文部分内容由 AI 辅助生成，以下为更新记录。

<details>
<summary>📝 更新记录（最近：2026-01-07 18:29:30）</summary>

| 时间 | 操作 | 说明 | Agent |
|------|------|------|-------|
| 2026-01-07 18:29:30 | 修改 | 补充第三节示例代码，修正日期格式 | Claude Code 2.3.0 / claude-opus-4-8 |
| 2026-01-07 18:10:15 | 修改 | 更新字体方案描述 | Claude Code 2.3.0 / claude-opus-4-8 |
| 2026-01-06 12:00:00 | 创建 | 初次生成全文 | Claude Code 2.1.197 / deepseek-v4-pro[1m] |

</details>
```

### 字段说明

| 字段 | 格式 | 说明 |
|------|------|------|
| 时间 | `YYYY-MM-DD HH:mm:ss` | UTC+8（Asia/Shanghai），精确到秒 |
| 操作 | `创建` / `修改` / `排版` / `翻译` | 中文 |
| 说明 | 简短描述 | 创建写"初次生成全文"；修改写具体改动范围，不可留空 |
| Agent | `<名称> <版本> / <模型>` | 参见下方 Agent/模型信息 |

### `<summary>` 内容

- 始终显示 **最近一条** 记录的时间：`📝 更新记录（最近：2026-01-07 18:29:30）`
- 每次追加新记录后，更新 `<summary>` 中的时间为最新值

### 表格排序

- **倒序排列**：最新的记录在第一行，最早的在最后
- 追加新记录时，在表格第一行（表头下方）插入新行
- 仅有一条记录时，`<summary>` 中不显示"最近："前缀，直接写 `📝 更新记录（2026-01-06 12:00:00）`

### Agent/模型信息

按当前运行环境获取：

- **Claude Code**：运行 `claude --version` 获取版本号；模型取当前会话信息中的模型名称（含方括号后缀如 `[1m]`）。
- **Codex**：运行 `codex --version` 获取版本号；模型优先取当前会话信息。
- 某项无法可靠获取时写 `unknown`，不推测、不编造。

同一会话中 Agent 和模型信息保持不变，首次获取后在本会话内缓存复用，不重复探测。

### 追加规则

1. **新建文章**：在正文最后（所有内容之后）创建完整的更新记录块，首行为 `创建` 操作，表格只有一行
2. **修改文章**：
   - 找到文末的 `<details>` 块，在表格第一行（表头下方）插入新行
   - 更新 `<summary>` 中的时间为最新值
   - 若文章尚不存在更新记录块，在文末新建
   - `修改` 的说明必须写出具体改动（如"补充第三节示例代码"），不可只写"修改"
3. 同一次提交的多处改动合并为一条记录

### 示例：仅有一条记录的新文章尾部

```markdown
> 本文由 Claude Code 辅助生成。

<details>
<summary>📝 更新记录（2026-01-06 12:00:00）</summary>

| 时间 | 操作 | 说明 | Agent |
|------|------|------|-------|
| 2026-01-06 12:00:00 | 创建 | 初次生成全文 | Claude Code 2.1.197 / deepseek-v4-pro[1m] |

</details>
```

## 六、字体与样式约定

- 字体方案：自托管 Noto 变量字体（`Noto Serif Variable` / `Noto Serif SC Variable` / `Noto Sans Mono Variable`），unicode-range 分包
- 字体文件位于 `public/fonts/`，样式入口在 `src/layouts/Layout.astro` 的 `<head>`
- 自定义样式在 `src/styles/` 中修改，主题色变量在 `src/styles/theme.css`
- 任何涉及字体加载顺序的改动，必须在 `pnpm build` 后检查是否有 CSS `@import` 顺序警告
