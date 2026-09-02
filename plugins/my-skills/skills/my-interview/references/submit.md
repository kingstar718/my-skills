# LeetCode 提交（可选）

本地测试全绿后，可提议把题解提交到真实 OJ 验证隐藏用例。默认 leetcode.cn（本机直连 leetcode.com 返回 403）。

## 前提：Cookie

浏览器登录 leetcode.cn → F12 → Application → Cookies → 复制 `LEETCODE_SESSION` 与 `csrftoken` 的值。三种给法任选：

1. **整段粘贴（最简单）**：把浏览器复制的整段 Cookie 字符串给教练，用 `--cookie "..."` 传入，脚本自动提取 `LEETCODE_SESSION` 与 `csrftoken`。也可用 `--session` / `--csrf` 或 `LEETCODE_SESSION` / `LEETCODE_CSRFTOKEN` 环境变量单独传，单次命令用完即弃、不落盘。
2. **交互式粘贴**：直接运行脚本，提示时粘贴（不回显），值不经过命令行和文件。
3. **配置文件（持久）**：写入 `~/.my-interview/leetcode_cookies.json`：

```json
{
  "LEETCODE_SESSION": "eyJ...",
  "csrftoken": "32 位字符串"
}
```

- 无论哪种方式，cookie 都是账号凭证，不要提交进 git 仓库；过期后重取（一般数周~数月），脚本报「缺少 Cookie」或 HTTP 403 即提示用户更新。

## 提交内容要求

LeetCode 只接受 `class Solution { ... }`，不能含 `main` 与自测辅助类。转换规则：

- 练习文件 `P27RemoveElement.java` → 生成提交文件：类名改 `Solution`、保留解题方法、删 `main`/辅助方法。
- 含中文注释一般可提交；若报编译编码错误，去掉注释再交。

## 用法

```bash
python <skill目录>/scripts/leetcode_submit.py --slug remove-element --file D:\projects\interview-wiki\practice\P27RemoveElementSolution.java
```

- `--slug`：从题库文件名取，如 `27-remove-element.md` → `remove-element`。
- `--site`：默认 `cn`；国际站用 `global`（需能访问 leetcode.com）。
- 退出码：0=AC；1=判题未过（WA/TLE/CE 等，会打印用例或编译错误）；2=配置/网络异常。

## 风险

- 属非官方接口，违反 LeetCode ToS；个人练习低风险，别高频提交。
- 判题结果用于复盘（写 log.md），不代表每题都必须交。