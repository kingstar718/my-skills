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
src/content/pages/   # 独立页面（about.md 等）
docs/templates/      # 模板参考（不对外发布，draft: true）
```

### Frontmatter Schema

每篇文章头部必须包含以下 YAML frontmatter，与 `src/content.config.ts` 的 Zod schema 对应：

```yaml
---
author: kingstar718                          # 固定
pubDatetime: 2026-07-07T12:00:00Z            # 首次发布时间（ISO 8601，UTC）
modDatetime: 2026-07-07T15:30:00Z            # 最后修改时间（可选，修改文章时更新）
title: 文章标题                                # 必填
featured: false                              # 是否精选（默认 false）
draft: false                                 # 草稿不公开（true/false）
tags:                                        # 标签数组，至少一个
  - tag1
  - tag2
description: 文章摘要，会出现在卡片和 OG 描述中    # 必填
---
```

### 标签规范

- 标签用小写英文或中文，不用混合语言
- 技术类：`astro`、`typescript`、`css`、`font`、`markdown`
- 主题类：`折腾`、`博客`、`阅读`
- 新增标签时，先在已有文章中 grep 确认是否已存在同义标签
- 每篇文章标签建议 2-4 个，不宜过多

### Markdown 写作约定

- **标题层级**：正文从 `##` 开始（`h1` 由 `title` 渲染），层级不超过 `####`
- **链接**：站内文章用相对路径 `[标题](/posts/slug)`；外部链接用 `[文字](https://...)`
- **图片**：放 `src/assets/images/`，文章中用 `![alt](/src/assets/images/xxx.png)` 引用
- **代码块**：必须标记语言 ` ```typescript `，行内代码用单反引
- **中文排版**：中英文之间加空格；中文语句用全角标点
- **日期格式**：章节标题用 `## 2026-07-07 — 小节标题` 的格式

### 文件命名

- 文件名 = 文章 slug，小写英文 + 连字符：`astro-paper-customization-journey.md`
- 中文标题通过 `title` frontmatter 表达，不放在文件名中

## 二、文章生成与修改

### 新建文章

1. 确认 `src/content/posts/` 下没有同名文件
2. 按上述 Frontmatter Schema 填写元数据：
   - `pubDatetime` 取当前 UTC 时间（`new Date().toISOString()`）
   - `modDatetime` 初始与 `pubDatetime` 相同或省略
   - `draft: false`（如果准备发布）
3. 正文按 Markdown 写作约定组织
4. 在文章末尾追加更新记录块（见「六、AI 生成与更新记录」），记录本次创建操作
5. 写完后本地预览验证

### 修改已有文章

1. 读取目标文章的完整内容，理解现有结构和风格
2. 检查文末是否存在 `<!-- AI-UPDATE-HISTORY` 块；不存在则创建，存在则在末尾追加本次记录
3. 修改正文内容
4. 更新 `modDatetime` 为当前 UTC 时间
5. 如果新增了标签，检查是否与已有标签体系一致

### 模板参考

`docs/templates/posts/` 下保留 AstroPaper 原版模板文章（已设 `draft: true`），写作格式或功能用法可参考：
- `examples/tailwind-typography.md` — 排版功能测试
- `how-to-update-dependencies.md` — 工具类文章格式

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
| frontmatter 校验失败 | Zod schema 不匹配 | 检查 `pubDatetime` 是否为 Date 类型、`tags` 是否为数组 |
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

2. Commit message 格式：

```text
<type>(post): <中文简述>

Agent: Claude Code
Model: <当前模型>
```

`type` 按实际操作选择：`feat`（新文章）、`fix`（修正内容）、`refactor`（结构调整）、`chore`（格式/标签修正）。

3. 文章中必须同步追加更新记录（见第六节），与 commit message 互相对应。

3. 推送：

```bash
git push origin main
```

### 部署

项目无自动部署 workflow（CI 只做 lint + build 校验）。推送后需手动触发部署或使用 Vercel/Railway 等平台的 Git 集成自动部署 `dist/` 目录。

### 发布前检查清单

- [ ] 本地 `pnpm build` 通过（0 errors / 0 warnings）
- [ ] `pnpm dev` 预览文章渲染效果
- [ ] 检查暗色模式下代码块和排版是否正常
- [ ] 标签不重复、不与已有同义标签冲突
- [ ] `draft: false`（准备公开发布）
- [ ] `modDatetime` 已更新（修改文章时）
- [ ] commit message 包含 Agent/Model footer
- [ ] 文末 `<!-- AI-UPDATE-HISTORY` 块已追加本次操作记录
- [ ] 修改文章时 `modDatetime` 已更新

## 五、AI 生成与更新记录

每篇由 AI 创建或修改的文章，必须在文末维护一个 HTML 注释块，记录每次操作的元信息。此块对读者不可见，但保留在源文件中供审计。

### 更新记录块格式

```html
<!-- AI-UPDATE-HISTORY
2026-07-07T12:00:00Z | created: 初次生成全文 | Claude Code 2.1.197 / deepseek-v4-pro[1m]
2026-07-08T09:30:00Z | modified: 补充第三节示例代码,修正日期格式 | Claude Code 2.3.0 / claude-opus-4-8
2026-07-09T14:00:00Z | modified: 更新字体方案描述 | Claude Code 2.3.0 / claude-opus-4-8
-->
```

每行一条记录，格式：

```text
<ISO 8601 UTC 时间> | <操作类型>[: <具体改动>] | <Agent 名称及版本> / <模型标识>
```

### 操作类型

| 类型 | 场景 |
|------|------|
| `created` | 首次生成文章全文 |
| `modified` | 修改已有内容（必须简述改动范围） |
| `formatted` | 仅格式/排版修正，不改变内容 |
| `translated` | 翻译操作 |

### Agent/模型信息

按当前运行环境获取：

- **Claude Code**：运行 `claude --version` 获取版本号；模型取当前会话信息中的模型名称（含方括号后缀如 `[1m]`）。
- **Codex**：运行 `codex --version` 获取版本号；模型优先取当前会话信息。
- 某项无法可靠获取时写 `unknown`，不推测、不编造。

同一会话中 Agent 和模型信息保持不变，首次获取后在本会话内缓存复用，不重复探测。

### 追加规则

1. **新建文章**：文末追加更新记录块，首行为 `created` 操作
2. **修改文章**：
   - 若文末已存在 `<!-- AI-UPDATE-HISTORY` 块，在最后一个 `-->` 前追加新行
   - 若不存在，在文末新建该块并追加本次记录
   - `modified` 行必须简述改动范围（如"修正第三节日期格式"），不可只写 `modified`
3. **多次修改**：每条修改独立一行，时间戳准确到秒，按时间升序排列
4. 此块始终放在文章最后，位于所有正文和链接之后

### 示例：新文章的完整尾部

```markdown
---

> 本文由 Claude Code 辅助生成，源文件保留完整更新记录。

<!-- AI-UPDATE-HISTORY
2026-07-07T12:00:00Z | created: 初次生成全文 | Claude Code 2.1.197 / deepseek-v4-pro[1m]
-->
```

## 六、字体与样式约定

- 字体方案：自托管 Noto 变量字体（`Noto Serif Variable` / `Noto Serif SC Variable` / `Noto Sans Mono Variable`），unicode-range 分包
- 字体文件位于 `public/fonts/`，样式入口在 `src/layouts/Layout.astro` 的 `<head>`
- 自定义样式在 `src/styles/` 中修改，主题色变量在 `src/styles/theme.css`
- 任何涉及字体加载顺序的改动，必须在 `pnpm build` 后检查是否有 CSS `@import` 顺序警告
