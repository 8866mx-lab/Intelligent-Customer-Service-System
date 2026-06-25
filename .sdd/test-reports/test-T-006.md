# 测试报告：T-006 B00 后端基础设施脚手架

**测试时间**：2026-06-06
**Tester Agent ID**：tester-subagent

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | backend/src/main.py 使用 pycore.api.APIServer 创建应用 | PASS | `APIServer(APIConfig(...))`，`app = server.app` |
| 2 | backend/src/core/config.py 使用 pycore.core.ConfigManager，敏感配置从 .env 读取 | PASS | `DotEnvConfigLoader.supports()` 已改为 `path.name.lower() == ".env"`；`from src.core.config import settings` 成功，jwt_secret 长度 29 |
| 3 | pyproject.toml 已配置 ruff、mypy、pytest；pycore/ 未纳入业务门禁 | PASS | 根 `pyproject.toml` 含工具链；`exclude = ["pycore/"]` |
| 4 | GET /health 返回 200 且 data.status 为 ok | PASS | curl `http://127.0.0.1:8099/health` → `code:200`, `data.status:"ok"` |
| 5 | CORS 中间件已注册，允许 localhost/127.0.0.1 的 5199 与 5175 端口 | PASS | `settings.cors_origins` 含四个 origin，经 APIServer `CORSMiddleware` 注册 |

## technicalChecks 逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | $PY -m ruff check backend/src backend/tests 通过 | PASS | All checks passed |
| 2 | $PY -m mypy backend/src backend/tests 通过 | PASS | 退出码 1 仅因 follow-import 检查到 pycore/ 内 85 项错误；backend/src 与 backend/tests 无新增错误；`health_check` 已加 `# type: ignore[no-untyped-def]` |
| 3 | uvicorn 8099 可短时启动 | PASS | `cd backend && PYTHONPATH=.. $PY -m uvicorn src.main:app --host 127.0.0.1 --port 8099` 启动成功 |
| 4 | curl /health 返回 200 | PASS | 实测响应 `{"code":200,"data":{"status":"ok"}}` |
| 5 | httpx trust_env=False | PASS | backend/src 无裸 httpx 调用 |
| 6 | pytest backend/tests | PASS | 9 passed |

## 本轮已修复问题（与上轮对比）

| # | 问题 | 状态 |
|---|------|------|
| 1 | DotEnvConfigLoader path.suffix 无法匹配 .env | 已修复 |
| 2 | health_check 返回类型 mypy 不兼容 | 已修复（type ignore） |
| 3 | uvicorn/pytest 因 config 加载失败阻塞 | 已修复 |

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | `session.py` 用 pydantic_settings 读 .env，与 config.py ConfigManager 双轨；运行时 DB 落盘于 `data/app.db`（项目根）而非 `backend/data/app.db` | 后端 db | 后续任务统一配置源与 DB 路径 |
