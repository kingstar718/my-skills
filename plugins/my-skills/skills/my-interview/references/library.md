# 内容库配置与检索映射

my-interview 的题目与答案来自本地 interview-wiki 内容库。本文件记录库地址与寻址规则。

## 库地址

```yaml
local_dir: D:\projects\interview-wiki
git_url: https://github.com/kingstar718/interview-wiki.git
cache_dir: ~/.my-interview/interview-wiki   # git 回退时的克隆目标
```

> 首次通过 git 或用户输入拿到有效库后，把实际路径/地址回写到上面对应字段（`local_dir` 指向可用目录、必要时更新 `git_url`），下次直接命中本地。

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
