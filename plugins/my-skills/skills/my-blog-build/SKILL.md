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
4. 写完后本地预览验证

### 修改已有文章

1. 读取目标文章的完整内容，理解现有结构和风格
2. 修改正文内容
3. 更新 `modDatetime` 为当前 UTC 时间
4. 如果新增了标签，检查是否与已有标签体系一致

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

2. Commit message 遵循本仓库 AGENTS.md 规范：

```text
<type>: <中文简述>

Agent: Claude Code
Model: <当前模型>
```

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

## 五、字体与样式约定

- 字体方案：自托管 Noto 变量字体（`Noto Serif Variable` / `Noto Serif SC Variable` / `Noto Sans Mono Variable`），unicode-range 分包
- 字体文件位于 `public/fonts/`，样式入口在 `src/layouts/Layout.astro` 的 `<head>`
- 自定义样式在 `src/styles/` 中修改，主题色变量在 `src/styles/theme.css`
- 任何涉及字体加载顺序的改动，必须在 `pnpm build` 后检查是否有 CSS `@import` 顺序警告
