# 开发计划

> 设计阶段与开发阶段的衔接文件。所有开发进度以本文件为准。

## 一、功能清单总览

| 序号 | 功能编号 | 功能名称 | 一句话描述 | 对应页面 | 优先级 | 状态 |
|------|---------|---------|-----------|---------|--------|------|
| 1 | F-01-01 | 账号密码登录 | 输入账号密码进入系统 | P01 | MVP | 待开发 |
| 2 | F-01-02 | 登录态保持 | Token 有效期内免登录 | P01 | MVP | 待开发 |
| 3 | F-01-03 | 退出登录 | 清除登录态 | P01 | MVP | 待开发 |
| 4 | F-02-01 | AI 问答 | RAG 六步链路返回答案 | P02 | MVP | 待开发 |
| 5 | F-02-02 | 多轮对话 | 3 轮短期记忆上下文 | P02 | MVP | 待开发 |
| 6 | F-02-03 | 转人工 | 创建工单进入排队 | P02 | MVP | 待开发 |
| 7 | F-02-04 | 历史会话列表 | 左侧展示所有会话 | P02 | MVP | 待开发 |
| 8 | F-02-05 | 继续/只读历史 | 已完成会话禁止发送 | P02 | MVP | 待开发 |
| 9 | F-02-06 | 新建会话 | 创建空白对话 | P02 | MVP | 待开发 |
| 10 | F-02-07 | 页面跳转 | 顶部 Tab 切换 | P02 | MVP | 待开发 |
| 11 | F-03-01 | 工单列表 | 待处理/处理中/已完成分组 | P03 | MVP | 待开发 |
| 12 | F-03-02 | 查看工单 | 展示完整对话历史 | P03 | MVP | 待开发 |
| 13 | F-03-03 | 接单处理 | 手动接单变处理中 | P03 | MVP | 待开发 |
| 14 | F-03-04 | 人工回复 | 坐席文字回复员工 | P03 | MVP | 待开发 |
| 15 | F-03-05 | 智能回复 | RAG 生成 3 条候选 | P03 | MVP | 待开发 |
| 16 | F-03-06 | 工单归类 | 预设分类标签 | P03 | MVP | 待开发 |
| 17 | F-03-07 | 结束工单 | 锁定会话只读 | P03 | MVP | 待开发 |
| 18 | F-03-08 | 页面跳转 | 顶部 Tab 切换 | P03 | MVP | 待开发 |
| 19 | F-04-01 | 文件上传 | 上传 .md 文件 | P04 | MVP | 待开发 |
| 20 | F-04-02 | 文件列表 | 展示入库状态 | P04 | MVP | 待开发 |
| 21 | F-04-03 | 知识入库 | 四库并行写入 | P04 | MVP | 待开发 |
| 22 | F-04-04 | 入库详情 | 切块数/QA 数/四库状态 | P04 | MVP | 待开发 |
| 23 | F-04-05 | 删除文件 | 清除文件及索引 | P04 | MVP | 待开发 |
| 24 | F-04-06 | 页面跳转 | 顶部 Tab 切换 | P04 | MVP | 待开发 |

## 二、数据契约摘要

> 完整数据契约见 `PRD.md` 第 7 章「数据契约确认清单」。
> 统一响应格式与接口字段定义见 `api-contracts.md`（唯一权威源）。

核心实体：`users`、`user_profile`、`conversations`、`messages`、`tickets`、`kb_files`、`kb_vectors`、`kb_keywords`、`kb_metadata`、`kb_qa`

## 二点五、外部服务与测试权限清单

> 开发硬门禁：真实 Key 不写入本文档，只记录字段名与配置状态。

| 服务 | 用途 | 配置项字段 | MVP 必需 | Tester 完整联调权限 | 缺失时策略 | 状态 |
|------|------|------------|----------|--------------------|------------|------|
| 百炼 LLM (qwen-plus) | Query改写、意图识别、反问、槽位填充、生成、QA抽取 | `DASHSCOPE_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL` | 是 | 用户提供的测试 Key + 可调用额度 | Mock 固定回复，标记降级验收 | **已确认供应商，Key 开发前由用户提供** |
| 百炼 Embedding (text-embedding-v3) | 向量召回、QA匹配、文档入库 | `DASHSCOPE_API_KEY`, `EMBEDDING_MODEL` | 是 | 同源 Key | Mock 随机向量，标记降级验收 | **已确认供应商，Key 开发前由用户提供** |
| 百炼 Rerank (gte-rerank) | RAG 重排 | `DASHSCOPE_API_KEY`, `RERANK_MODEL` | 是 | 同源 Key | 跳过重排，RRF Top-K 直出 | **已确认供应商，Key 开发前由用户提供** |
| SQLite | 业务数据 + 四库 | `DATABASE_URL` | 是 | 本地文件 | 默认 `sqlite:///./data/app.db` | **已确认** |
| 本地文件存储 | .md 上传 | `UPLOAD_DIR` | 是 | 本地目录 | 默认 `./uploads` | **已确认** |
| WebSocket | 实时消息 | 无外部依赖 | 是 | 本地服务 | 降级轮询 | **已确认** |

`.env.example` 模板见 `PRD.md` 第 8 章。

## 三、前端开发清单

### 前端技术选型

| 层级 | 选择 | 说明 |
|------|------|------|
| 框架 | React 18 | 业务型 Web App |
| 语言 | TypeScript | 组件、service、DTO 类型化 |
| 构建 | Vite | 开发代理、构建 |
| 路由 | react-router-dom v6 | 页面路由 + 鉴权守卫 |
| 状态 | Zustand | 登录态、全局 UI |
| 请求 | Axios | 统一实例、拦截器 |
| 组件库 | Ant Design 5 | 桌面 Web |
| 工程化 | ESLint + Prettier + tsc + build | 自动验收 |

### 页面开发清单

| 序号 | 页面 | 路由 | 涉及功能 | Mock 数据来源 | 状态 |
|------|------|------|---------|--------------|------|
| P01 | 登录页 | `/login` | F-01-01~03 | `api-contracts.md` POST /api/auth/login | 待开发 |
| P02 | 员工端 | `/employee` | F-02-01~07 | conversations、messages API | 待开发 |
| P03 | 坐席端 | `/agent` | F-03-01~08 | tickets、suggest API | 待开发 |
| P04 | 知识库 | `/knowledge` | F-04-01~06 | kb/files API | 待开发 |
| — | AppShell | `/` | 导航+鉴权 | auth/me API | 待开发 |

### 关键组件

| 组件 | 原型参考 | 优先级 |
|------|----------|--------|
| `AppShell` | prototypes 顶部导航 | P0 |
| `ChatBubble` + `CitationCard` | prototypes 02-employee 引用卡片 | P0 |
| `ConversationList` | prototypes 02 左栏 | P0 |
| `TicketList` | prototypes 03 左栏分组 | P0 |
| `SuggestPanel` | prototypes 03 智能回复候选 | P1 |
| `KbUpload` + `KbTable` | prototypes 04 | P0 |

### 前端自动验收标准

- [ ] 所有页面 UI 与 `docs/prototypes/` 原型一致
- [ ] 所有页面使用 Mock 数据可正常交互
- [ ] Mock 数据格式与 `api-contracts.md` 完全一致
- [ ] `VITE_USE_MOCK=true` 时全流程可走通
- [ ] ESLint + type-check + build 通过

> 前端 Mock 完成后触发**用户门禁**验收 UI/UX；确认后进入后端基础设施开发。

## 四、后端开发清单

| 序号 | 任务 | 依赖 | 对应接口 | 状态 |
|------|------|------|---------|------|
| B00 | 基础设施脚手架 | 无 | GET /health | 待开发 |
| B01 | 数据库模型与迁移 | B00 | — | 待开发 |
| B02 | 认证模块 JWT | B01 | POST /api/auth/login, GET /api/auth/me | 待开发 |
| B03 | 会话 CRUD | B02 | GET/POST /api/conversations, GET /{id} | 待开发 |
| B04 | 知识库上传与入库 | B01 | POST /api/kb/upload, GET /api/kb/files | 待开发 |
| B05 | RAG Pipeline 核心 | B04 | — | 待开发 |
| B06 | 发消息 + AI 问答 | B03, B05 | POST /conversations/{id}/messages | 待开发 |
| B07 | 长短期记忆 | B06 | — | 待开发 |
| B08 | 转人工 + 工单 | B03 | POST /transfer, GET/POST tickets | 待开发 |
| B09 | 坐席回复 + 智能回复 | B08, B05 | messages, suggest | 待开发 |
| B10 | 工单归类/结束 | B08 | PATCH /api/tickets/{id} | 待开发 |
| B11 | WebSocket 实时推送 | B09 | WS /ws/messages | 待开发 |
| B12 | 知识库删除/重试 | B04 | DELETE, POST retry | 待开发 |

### 后端任务验收规则

- 基础设施基于 **pycore**：`ConfigManager`、`APIServer`、db 模板
- B00~B01 自动连续执行，不触发用户门禁
- B00 验收：ruff/mypy 通过、`GET /health` 返回 200
- 业务任务验收：`VITE_USE_MOCK=false` 真实联调 + Tester 验证
- 百炼 API 缺失时：RAG 任务标记 Mock 降级验收，不得宣称真实联调通过

## 五、功能详情（开发时逐个展开）

### F-02-01 AI 问答（核心）

- **后端**：`services/rag/pipeline.py` 实现六步链路
- **前端**：发送消息后展示 AI 气泡 + CitationCard
- **联调**：Mock 与真实 RAG 响应结构一致（`metadata.response_type`, `citations`）
- **降级**：无 Key 时 `response_type: mock`

### F-04-03 知识入库

- **后端**：异步任务切块 → 四库并行写入 → 状态轮询
- **前端**：上传后列表 status 从 processing → completed
- **联调**：上传真实 .md，验证 chunk_count / qa_count

### F-02-03 + F-03 转人工闭环

- **链路**：transfer → ticket pending → accept → messages → complete → 只读
- **WebSocket**：new_message + ticket_status_changed 事件

---

## 六、开发顺序建议

### 阶段 1：前端 MVP（Mock，用户先验收 UI/UX）

1. 初始化 `frontend/`（Vite + React + TS + Ant Design）
2. 实现 AppShell + 路由守卫
3. P01 登录页 Mock
4. P02 员工端 Mock（含引用卡片）
5. P03 坐席端 Mock（含智能回复面板）
6. P04 知识库 Mock
7. **用户门禁**：对照原型验收 UI/UX

### 阶段 2：后端基础设施（自动连续，无用户门禁）

1. 初始化 `backend/`（pycore 脚手架）
2. 数据库表创建 + 种子用户
3. JWT 认证中间件
4. `GET /health` 验收

### 阶段 3：逐功能闭环（每功能完成后联调验收）

推荐顺序：

```text
B02 登录 → B04 知识库入库 → B05~B06 RAG问答 → B03 会话管理
→ B08 转人工 → B09 坐席回复 → B10 结束工单 → B11 WebSocket
```

每完成一项：前端对应 service 切 `VITE_USE_MOCK=false`，用户验证。

### 阶段 4：E2E 回归

完整路径：登录 → 上传知识库 → 员工提问 → 转人工 → 坐席接单回复 → 结束工单

---

## 七、里程碑与验收

| 里程碑 | 交付物 | 验收人 |
|--------|--------|--------|
| M0 设计完成 | PRD + api-contracts + Plan + prototypes | 用户 ✅ |
| M1 前端 Mock | 4 页面可交互 | 用户 |
| M2 后端基础 | health + DB + auth | Agent 自动 |
| M3 知识库+RAG | 上传入库 + AI 问答 | 用户 + Tester |
| M4 转人工闭环 | 工单全流程 + WS | 用户 + Tester |
| M5 全系统 E2E | 端到端无阻塞 Bug | 用户 |
