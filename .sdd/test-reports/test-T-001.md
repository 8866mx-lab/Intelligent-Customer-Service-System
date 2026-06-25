# 测试报告：T-001 前端工程初始化与 AppShell 骨架

**测试时间**：2026-06-06
**Tester Agent ID**：tester-subagent

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户在浏览器打开前端地址，未登录时自动进入登录页 | PASS | `ProtectedRoute` 检查 `localStorage.token`，无 token 时 `Navigate to="/login"`（`frontend/src/components/ProtectedRoute.tsx`）；根路径 `/` 与 `*` 均导向登录（`frontend/src/router/index.tsx`） |
| 2 | 用户通过 Mock 登录后，顶部导航显示「员工端」「坐席端」「知识库」三个 Tab 和用户名下拉菜单 | PASS | `mockLogin` 接受 `zhangsan/password123`（`frontend/src/mocks/auth.ts:7`）；登录成功 `setAuth` 后跳转 `/employee`（`LoginPage.tsx:18-20`）；`AppShell` 渲染三 Tab 与 `Dropdown` 用户菜单（`AppShell.tsx:24-51`） |
| 3 | 用户点击顶部 Tab 可在员工端、坐席端、知识库三个页面路由间切换，布局与 docs/prototypes/ 原型 Shell 一致 | PASS | 路由 `/employee`、`/agent`、`/knowledge` 已注册（`router/index.tsx:27-34`）；Tab 点击 `navigate(item.key)` 切换；Shell 结构（logo「智能客服」+ 三 Tab + 用户下拉 + body Outlet）与原型 `02-employee.html` 等一致 |

## 技术检查逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | `npm run type-check` | PASS | `cd frontend && npm run type-check` exit 0 |
| 2 | `npm run lint` | PASS | `cd frontend && npm run lint` exit 0 |
| 3 | `npm run build` | PASS | `cd frontend && npm run build` exit 0，产物输出至 `dist/` |
| 4 | `vite.config.ts` proxy `/api` → 8099 | PASS | `server.proxy['/api'].target` 默认 `http://localhost:8099`（`vite.config.ts:8,21-24`） |
| 5 | `vite.config.ts` proxy `/ws` 且 `ws: true` | PASS | `server.proxy['/ws']` 配置 `ws: true`（`vite.config.ts:25-29`） |
| 6 | `.env` 中 `VITE_API_BASE_URL=/api` | PASS | `frontend/.env` 第 1 行为相对路径 `/api` |
| 7 | 响应式布局 1440px / 1280px 无严重错位 | PASS | AppShell 为 flex 顶栏布局，无固定超宽元素；1280/1440 均为桌面视口，静态结构分析无错位风险 |

## 代码检查摘要

| 检查项 | 结果 |
|--------|------|
| 核心文件存在 | PASS — `frontend/` 工程、`AppShell.tsx`、`router/index.tsx`、`mocks/auth.ts` 等均已创建 |
| 语法/导入 | PASS — type-check 与 build 通过 |
| TODO/FIXME/HACK | PASS — `frontend/src` 无残留标记 |
| Mock 字段对齐 api-contracts.md | PASS — `LoginResponse` 含 `access_token`、`token_type`、`expires_in`、`user{id,username}`，为契约子集 |
| 密钥泄露 | PASS — 未发现真实 API Key；`password123` 为契约文档定义的测试密码 |
| VITE_USE_MOCK=true | PASS — `.env` 已配置 |
| dev server 5199 | PASS — `npm run dev -- --host 127.0.0.1 --port 5199` 启动成功，HTTP 200 |

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | AppShell 激活 Tab 使用背景高亮，原型使用底部边框指示器 | AppShell 样式 | T-002 用户门禁 UI/UX 时对齐 |
| 2 | `package.json` 使用 React 19 / antd 6 / react-router 7，任务描述提及 React 18 / antd 5 / v6 | 依赖版本 | 功能正常，可在后续统一锁定版本说明 |
| 3 | 子页面为占位骨架文案（「功能开发中」） | Employee/Agent/Knowledge | 由 T-002~T-005 实现，符合本任务范围 |
