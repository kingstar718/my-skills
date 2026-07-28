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
description: 一句话摘要，≤45 字             # 必填，见下
featured: false                              # 是否精选（可选，默认 false）
draft: false                                 # 草稿不公开（可选）
aiGenerated: true                            # 正文由 AI 辅助生成（可选，见下）
canonicalURL: https://...                    # 规范链接（可选，通常不填）
updates: []                                  # 更新记录（可选，见第五节）
---
```

字段以 `src/content.config.ts` 的 Zod schema 为准，schema 里没有的键会被静默丢弃。

**`pubDatetime` 是全站唯一的日期字段**：排序和页面显示都读这一个值，所以两者永远一致。不存在 `modDatetime`。

格式是 `"YYYY-MM-DD HH:mm"`，**按站点时区（Asia/Shanghai）解读，写的就是页面上显示的值**——不要再手算 UTC 偏移。**必须加引号**：不加引号且带秒的写法会被 YAML 直接解析成时间戳，绕过 schema 的时区处理。写错格式时构建会失败并提示正确写法，不会静默出错。

**`description` 必须 ≤45 字**：它出现在时间线的每一条下面，超过 45 字在 768px 的正文宽度里就会折行，几篇叠在一起首页就糊成一片。schema 有 `max(45)` 校验，超了构建直接失败。写不下说明还没提炼到位——只留这篇最独特的那一点，不要复述标题，也不要罗列全文要点。

**`aiGenerated` 标记正文是否由 AI 辅助生成**：为 `true` 时，时间线和文章页会在标题右侧渲染一个很轻的 `AI` 角标（`src/components/AiBadge.astro`）。**AI 生成或重写正文时必须写 `true`**，人自己写的写 `false` 或省略——两边都要显式表态，不设默认值就是为了避免默认值把哪一边标错。标记不进 `title` 字符串，因此 `<title>`、RSS 标题和 pagefind 索引都不受影响，不要改用在标题里加 `#ai` 之类的写法。

短文（`src/content/notes/`）的 schema 更窄，只有 `pubDatetime`（必填）和 `draft`（可选）——没有 `title` 也没有 `aiGenerated`，写了也不会渲染。

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
   - `aiGenerated: true`（正文由你生成时；人自己写的写 `false`）
3. 正文按 Markdown 写作约定组织
4. 在 frontmatter 的 `updates` 里写第一条记录（见「五、AI 生成与更新记录」）
5. 写完后本地预览验证

### 修改已有文章

1. 读取目标文章的完整内容，理解现有结构和风格
2. 在 frontmatter 的 `updates` 数组开头插入本次记录；数组不存在就新建
3. 修改正文内容
4. **`pubDatetime` 默认不动**——修改的痕迹由 `updates` 承载，日期字段保持文章的发布时间。只有在正文有实质重写、确实希望这篇重新回到时间线顶部时才更新它（例如「改造日志」这类持续更新的文章）。改错别字、修失效引用不要动日期，否则老文章会因为一处小修就顶上首页

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
| `description 控制在 45 字以内` | 摘要太长 | 精简到 45 字内，时间线上只占一行 |
| 日期显示或排序不对 | `pubDatetime` 写错 | 全站只有这一个日期字段，排序和显示都读它；日常修改不要动它，改动痕迹由 `updates` 承载 |
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

3. frontmatter 的 `updates` 必须同步追加记录（见第五节），与 commit message 互相对应。

4. 推送：

```bash
git push origin main
```

### 部署

推到 `main` 后 Cloudflare Pages 会自动构建上线，仓库里没有部署 workflow。`.github/workflows/ci.yml` 只做校验（内容收录检查、lint、format:check、build），`push` 到 main 和 pull request 都会触发——手机端发短文不会先本地构建，CI 是唯一的拦截点。

### 发布前检查清单

- [ ] 本地 `pnpm build` 通过（0 errors / 0 warnings）
- [ ] `pnpm dev` 预览文章渲染效果
- [ ] 检查暗色模式下代码块和排版是否正常
- [ ] frontmatter 只含 schema 里有的字段（没有 `author`/`modDatetime`/`tags`/`timezone`）
- [ ] `description` ≤45 字，时间线上是一行
- [ ] `draft: false`（准备公开发布）
- [ ] `aiGenerated` 与实际情况一致（AI 写的 `true`，人写的 `false`）
- [ ] 修改文章时 `pubDatetime` **保持不动**（除非是实质重写、确实要顶回时间线顶部）
- [ ] commit message 包含 `AI-Generated-By` footer
- [ ] frontmatter 的 `updates` 已在数组开头追加本次操作
- [ ] 文章已通读复验（语法、逻辑、术语一致性）

## 五、AI 生成与更新记录

每篇由 AI 创建或修改的文章，都要在 frontmatter 的 `updates` 数组里追加一条记录。
它是元数据，**不写在正文里**——`src/components/PostUpdates.astro` 会把它渲染成文章标题下方元信息行里的一个折叠块，与日期、目录并排（收起时只是一行「▸ 更新记录（N 条）」，展开才铺开列表）。

正文里不要再出现 `<details>` 更新记录块、`📝` 图标，也不要写「本文部分内容由 AI 辅助生成」这类提示行：AI 标记已经由 `aiGenerated` 在标题旁呈现，重复了。

### 格式

```yaml
updates:
  - datetime: "2026-01-07 18:29"
    action: 修改
    note: "补充第三节示例代码，修正日期格式"
    agent: "Claude Code 2.3.0 / claude-opus-4-8"
  - datetime: "2026-01-06 12:00"
    action: 创建
    note: 初次生成全文
    agent: "Claude Code 2.1.197 / deepseek-v4-pro[1m]"
```

### 字段说明

| 字段 | 格式 | 说明 |
|------|------|------|
| `datetime` | `"YYYY-MM-DD HH:mm"` | 与 `pubDatetime` 同一个校验器，**必须加引号**，按站点时区（Asia/Shanghai）解读。全站只有这一种日期格式，不带秒 |
| `action` | `创建` / `修改` / `排版` / `翻译` | schema 是枚举，写别的词构建会失败 |
| `note` | 简短描述 | 创建写「初次生成全文」；修改写具体改动范围。schema 校验非空 |
| `agent` | `<名称> <版本> / <模型>` | 含空格或 `/` 时加引号，参见下方 Agent/模型信息 |

含 `：`、`、`、`/` 等符号的中文串统一用双引号包起来，避免 YAML 解析歧义。

### 排序

**倒序排列**：最新的记录是数组第一项，最早的在最后。追加新记录时插到数组开头。

### Agent/模型信息

按当前运行环境获取：

- **Claude Code**：运行 `claude --version` 获取版本号；模型取当前会话信息中的模型名称（含方括号后缀如 `[1m]`）。
- **Codex**：运行 `codex --version` 获取版本号；模型优先取当前会话信息。
- 某项无法可靠获取时写 `unknown`，不推测、不编造。

同一会话中 Agent 和模型信息保持不变，首次获取后在本会话内缓存复用，不重复探测。

### 追加规则

1. **新建文章**：`updates` 只有一条，`action: 创建`
2. **修改文章**：在 `updates` 数组开头插入一条，`action` 按实际操作选；说明必须写出具体改动（如「补充第三节示例代码」），不可只写「修改」。数组不存在就新建
3. 同一次提交的多处改动合并为一条记录
4. **`pubDatetime` 不动**——改动痕迹由 `updates` 承载

## 六、字体与样式约定

- 字体方案：自托管 Noto 变量字体（`Noto Serif Variable` / `Noto Serif SC Variable` / `Noto Sans Mono Variable`），unicode-range 分包
- 字体文件位于 `public/fonts/`，样式入口在 `src/layouts/Layout.astro` 的 `<head>`
- 自定义样式在 `src/styles/` 中修改，主题色变量在 `src/styles/theme.css`
- 代码块的语法高亮配色是 `vitesse-light` / `vitesse-dark`（`astro.config.ts` 的 `shikiConfig`）；底色不取主题自带的纯白/纯黑，走 `theme.css` 的 `--code-background`
- 任何涉及字体加载顺序的改动，必须在 `pnpm build` 后检查是否有 CSS `@import` 顺序警告
