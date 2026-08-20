# 黑盒 HTTP E2E（pytest）

## 位置与形态

- 仓库根 `e2e/`，单文件 `test_*.py`（requests + pytest），不建 conftest；
- 不参与 Maven 构建；CI 单独 stage 运行 `pytest e2e -v`。

## 骨架要点

```python
HOST = "http://example.internal:1080"   # 固定测试环境地址（或环境变量注入）

def _service_up() -> bool: ...                   # 模块级探测一次
requires_service = pytest.mark.skipif(not SERVICE_UP, reason="环境不可达")

def _body_text(resp) -> str:                      # 断言用
    return json.dumps(resp.json(), ensure_ascii=False)
```

## 规则

- **可达性跳过**：模块级探测，环境不可达时跳过真机用例；CI 要统计 skip 数，避免静默假绿；
- **断言**：外层 envelope 字段名可能随框架变化，用 `json.dumps(..., ensure_ascii=False)` 包含中文业务 message 断言最稳；
- **数据隔离**：用例用唯一前缀（`__e2e_`）+ 时间戳，`finally` 里 best-effort 清理；
- **负向用例**：缺失参数、重复删除、未找到等失败路径与正向同等覆盖；
- 敏感信息（密钥）不要写死进文件，用环境变量/CI secret。
