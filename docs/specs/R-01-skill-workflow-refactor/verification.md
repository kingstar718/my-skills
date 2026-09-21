# R-01 验证记录

## 验证计划

| 项目 | 预期 | 状态 |
| --- | --- | --- |
| `spec-coding` 结构审查 | 支持紧凑/目录模式，AC 映射不限定单测 | 通过 |
| `spring-testing` 结构审查 | 测试层级按行为选择，项目特例按需披露 | 通过 |
| Skill 校验 | 两个 skill 均通过 `quick_validate.py` | 通过 |
| Plugin 校验 | `plugins/my-skills` 通过 `validate_plugin.py` | 通过 |
| 元数据检查 | JSON/YAML 可解析，两个 manifest 基础版本一致 | 通过（`1.10.0`） |
| 本次改动链接检查 | 相对 Markdown 链接均存在 | 通过 |
| 安装验证 | cachebuster 后重新安装并在新会话验证 | 待执行 |

## 最新结果

- `spec-coding`：`Skill is valid!`
- `spring-testing`：`Skill is valid!`
- `plugins/my-skills`：`Plugin validation passed`
- Windows 下运行 `quick_validate.py` 需要 `PYTHONUTF8=1`，否则 Python 默认 GBK 无法读取中文 UTF-8 文件。
- 当前 Codex 中 `my-skills@my-skills` 的来源是 Codex 临时 marketplace 克隆，而不是
  `D:\projects\my-skills`。按插件更新规则未直接覆盖或重装；需先明确是否切换为本地 marketplace，再在
  新会话验证实际触发和产物。

这里只保留当前结果；历史由 Git 和 CI 承担。
