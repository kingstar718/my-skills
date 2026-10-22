# 黑盒 HTTP E2E（pytest）

## 位置与形态

- 优先沿用仓库已有 E2E 目录、语言和辅助设施；没有约定时可在仓库根使用 `e2e/test_*.py`。
- 与 Maven 单元/集成测试分开执行，CI 是否作为门禁由流水线明确声明。

## 用例可读性

- 模块级 docstring：写清覆盖范围、响应约定（成功/失败 envelope）、运行方式与所需环境变量；
- 每个用例：描述性函数名 + 一行 docstring 说明“场景 + 预期结果”，断言可读，必要时带断言消息（失败时直接看到业务预期）；
- 重复的请求样板抽成 `_get`/`_post` 辅助函数，统一携带鉴权头与超时。

## 骨架要点

```python
import json
import os

import pytest

HOST = os.environ["E2E_BASE_URL"]

def _service_up() -> bool: ...                   # 模块级探测一次
requires_service = pytest.mark.skipif(not SERVICE_UP, reason="可选环境不可达")

def _body_text(resp) -> str:                      # 断言用
    return json.dumps(resp.json(), ensure_ascii=False)
```

## 规则

- **可达性策略**：本地可选环境不可达时允许显式跳过；若 CI/SIT/发布 stage 声明目标环境必备，探测失败
  必须让 stage 失败，不能通过 skip 假绿；
- **断言**：外层 envelope 字段名可能随框架变化，用 `json.dumps(..., ensure_ascii=False)` 包含中文业务 message 断言最稳；
- **响应契约先确认再断言**：按接口文档或实际契约断言字段层级，不把某个框架的 envelope 当成通用格式；
- **数据隔离**：用例用唯一前缀（`__e2e_`）+ 时间戳，`finally` 里 best-effort 清理；
- **负向用例**：缺失参数、重复删除、未找到等失败路径与正向同等覆盖；
- **目标与凭据**：地址、密钥和 token 不写死进文件，使用环境变量或 CI secret；日志避免输出敏感头；
- **证据回填**：若需求有 AC 映射，只记录目标环境、用例和报告链接，不把完整运行日志复制进 spec。
