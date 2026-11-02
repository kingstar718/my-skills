# 内容库配置与检索映射

interview 的题目与答案来自本地 interview-wiki 内容库。本文件记录库地址与寻址规则。

## 库地址

```yaml
local_dir: D:\projects\interview-wiki
git_url: https://github.com/kingstar718/interview-wiki.git
cache_dir: ~/.my-interview/interview-wiki   # git 回退时的克隆目标；不承载个人记录

# 练习工作区：相对内容库根，跨平台，不写盘符
practice_dir: practice
progress_file: content/个人记录/刷题进度.md   # 进度勾选 + 错题本
index_file: practice/README.md               # 题目索引 + 套路速查表
```

> 首次通过 git 或用户输入拿到有效库后，把实际路径/地址回写到上面对应字段（`local_dir` 指向可用目录、必要时更新 `git_url`），下次直接命中本地。
> 只回写 `local_dir` / `git_url`；`practice_dir`、`progress_file`、`index_file` 是相对内容库根的布局，不随机器改动。

## 练习工作区布局

| 字段 | 相对路径 | 角色 | 读写 |
|------|---------|------|------|
| `practice_dir` | `practice/` | 每题一个 `P{题号}{英文驼峰}.java` | 读+写 |
| `progress_file` | `content/个人记录/刷题进度.md` | 一阶段/二阶段勾选 + **错题本**表 | 改勾选、追加错题本行 |
| `index_file` | `practice/README.md` | 题目索引 + 套路速查表 + ✅ 清单 | 由 `practice_stats.py` 生成 |

写入边界：题库正文（`content/algorithms/`、`content/interview/`）只读；只允许改上面三类位置。

**统计校准**（在内容库根执行）：

```bash
python <skill目录>/scripts/practice_stats.py --check   # 只报偏差，退出码 1 表示有漂移
python <skill目录>/scripts/practice_stats.py --fix     # 重写速查表、✅ 标记与（N / M）计数
python <skill目录>/scripts/practice_stats.py --fix --fix-list   # 同时重生成摘要里的题名清单
```

- 真源：`progress_file` 的勾选（哪些题做完）与各套路章节的题目行（分母）。
- 脚本默认在当前目录找内容库，也可 `--wiki <dir>` 指定。


技能入口改名为 `interview` 后，继续复用已有练习目录、`~/.my-interview/` 下的缓存和 Cookie。
仅改变调用名称，不新建或搬移个人档案。

## 寻址顺序

1. **本地库优先**
   - `local_dir` 存在且含 `content/` 子目录 → 直接用，不联网。

2. **次 git**
   - 本地缺失或不含 `content/`：
     - `cache_dir` 已是有效克隆 → `git -C <cache_dir> pull --ff-only`，用它。
     - 否则 → `git clone <git_url> <cache_dir>`，用它；成功后把 `local_dir` 回写为 `cache_dir` 的绝对路径。
   - 网络/权限失败 → 转第 3 步。

3. **提示用户**
   - 提示：「未找到 interview-wiki 内容库，请提供本地目录路径或 git 仓库地址」。
   - 拿到目录 → 校验含 `content/` 后回写 `local_dir`。
   - 拿到 git 地址 → 回写 `git_url` 并回到第 2 步克隆。
   - 用户拒绝/无法提供 → 降级为「未接题库」模式：用自身知识出题讲解，并明确告知。

## 库结构与检索映射

以下路径均相对内容库根目录（`local_dir`）。

| 需求 | 用什么 |
|------|--------|
| 算法：按主题选题 | 题解 frontmatter `topics:`（13 个粗套路）+ `content/算法题索引.md` |
| 算法：按技术词选题 | `python scripts/outline.py --tech <技术词>`（44 个细技术词，不带参列全部+覆盖数） |
| 算法：高频/按公司选题 | `content/高频题目索引.md`（A. Top 算法题 / C. 各公司风格） |
| 算法：读某题题解 | `content/algorithms/problems/<题号>-<英文名>.md`（九节结构） |
| 八股：定位考点 | `python scripts/outline.py --grep <考点>`（全库标题+正文，命中标注所在小节） |
| 八股：看专题结构 | `python scripts/outline.py <文件名>`（打印标题树+行号） |
| 八股：读某专题 | `content/interview/<分类>/<专题>.md`（追问地图 + 各小节） |
| 八股：高频优先级/公司风格 | `content/高频题目索引.md`（B. 高频八股题 / C. 公司风格） |
| 知识点总览 | `content/知识点索引.md` |

- `scripts/outline.py` 纯标准库，`python`（本机 3.12）直接跑，即时输出不落盘。
- 命令行考点/文件名匹配大小写不敏感、支持部分匹配。

详细检索用法与内容结构见 [retrieval.md](retrieval.md)。
