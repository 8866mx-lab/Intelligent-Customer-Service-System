# 智能客服系统

企业内部智能客服 MVP：员工 AI 问答、转人工、坐席工单处理、知识库 RAG。

## 快速启动

详见 **[docs/startup.md](docs/startup.md)**（双 PowerShell 窗口：后端 8099 + 前端 5199）。

测试账号：`zhangsan` / `password123`

## 技术栈

- 前端：React + TypeScript + Vite + Ant Design
- 后端：FastAPI + PyCore + SQLite
- AI：百炼 DashScope（LLM / Embedding / Rerank）

## 目录

- `.sdd/`：任务、经验、Bugfix 记录
- `docs/`：PRD、API 契约、启动说明、原型
- `backend/` / `frontend/`：业务代码
- `scripts/`：`start-backend.ps1`、`start-frontend.ps1`
