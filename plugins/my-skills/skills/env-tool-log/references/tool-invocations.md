# 工具调用规则库

按工具分节。规则持续增长：`fail_log.py lessons --apply` 会把已修复失败的教训追加到数据目录 `lessons.md`，执行命令前应一并读取。

规则格式约定：

- 普通规则 `- 描述`：建议正确写法，写入 PreToolUse/UserPromptSubmit 提示。
- 高危规则 `- [BLOCK] <匹配文本> → 原因`：PreToolUse 命中时直接 deny 并给出原因。

## 通用

- 失败后先读 stderr 前几行再决定重试，不要盲改重跑。
- 命令设超时（PowerShell 用 `-TimeoutSec`，CLI 用 `--timeout`），避免长时间挂起。
- 查询优先 `rg` / 精确匹配，避免全目录递归 grep。
- 破坏性命令先确认目标路径，禁止对 `$HOME`、仓库根、`/` 等宽泛目录执行递归删除。
- [BLOCK] rm -rf $HOME → 危险：禁止对家目录执行 rm -rf
- [BLOCK] git reset --hard → 危险：未确认前禁止硬重置

## Java / JDK

- `javac` 认 `-version`，不认 `--version`（JDK8 报 "无效的标记"）。
- `java` 可执行文件取自 JDK 的 `bin/`，不要用 `jre/bin/`（jre 版 java.exe 启动报 "Could not create the Java Virtual Machine"）。
- 多 JDK 并存时先 `Get-Command java,javac` 确认来自同一套，再核对 JAVA_HOME。

## 搜索

- 优先 `rg`；Windows 上次选 `Select-String`，最后才是 `grep`。

## git

- 用 `git -C <仓库路径>`，避免 `cd` 进目录再执行。
- 提交前先 `git status --short`；只用 `git add <明确路径>`，不用 `git add -A` / `git add .`。
- 推送前先确认远程可达（`git ls-remote origin`），避免代理失效导致超时。

## 构建

- mvn：离线用 `-o`，指定模块用 `-pl <module>`，单模块构建避免全量。
- pnpm：开发依赖用 `pnpm add -D <pkg>`。

## Node

- 本机 PATH 可能混有多个 node 版本（如 nodejs18/20/24）：执行前用 `Get-Command node,npm,pnpm,yarn` 确认来自同一套，避免混用。

## 网络

- 出站 HTTPS 可能被环境阻断（如 github.com:443 超时）：先用 `Test-NetConnection host -Port 443` 确认，再判断是网络问题还是命令问题。
- 环境代理变量（HTTP_PROXY 等）指向失效代理时，先清除再测试直连。
