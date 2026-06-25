# 项目经验

> 当前项目长期有效的经验。  
> Developer / Tester / Bugfix 在任务完成后维护本文件。

---

## Harness 系统经验摘要

新项目开始时，Developer / Tester / Bugfix 需要同时参考：

- 当前项目经验：`.sdd/experience.md`
- 系统级经验：`<Harness 根目录>/memory/harness-experience.md`

---

### T-001: 前端工程初始化与 AppShell 骨架

- **经验**：
  - TypeScript 6.0+ 使用 `verbatimModuleSyntax` 选项时，类型必须使用 `import type` 或 inline `type` 导入语法（如 `import { Dropdown, type MenuProps } from 'antd'`）
  - `baseUrl` 在 TS 6.0+ 已弃用，需要添加 `"ignoreDeprecations": "6.0"` 来消除警告
  - React Router v7 的 Fast Refresh 要求组件和非组件导出分离，路由守卫等工具函数应单独文件导出
  - Vite 代理配置中的 WebSocket 代理必须显式设置 `ws: true`
  - npm install 在 Windows PowerShell 环境下可能需要较长时间（6分钟+），属于正常现象
- **避坑**：
  - 后续开发者在添加新的类型导入时，记得使用 `import type` 语法避免构建错误
  - 修改 vite.config.ts 或 .env 后必须重启 Vite 开发服务器才能生效
  - 路由守卫等工具组件应放在独立文件中，避免 Fast Refresh 警告

---

### T-002: P01 登录页 Mock 实现

- **经验**：
  - 登录页需要在 `useEffect` 中检查 localStorage 的 token，如果已登录则自动跳转到 `/employee`，避免已登录用户看到登录页
  - 原型文件中的样式细节（背景渐变色、卡片圆角、内边距、阴影等）必须精确对齐，不能凭感觉调整
  - Mock 数据的响应字段必须与 `docs/api-contracts.md` 完全一致，包括字段名、类型、嵌套结构
  - Windows PowerShell 不支持 `&&` 语法，需要使用分号 `;` 或单独执行命令
- **避坑**：
  - 已登录状态检查必须放在页面组件的 `useEffect` 中，不能只依赖路由守卫（路由守卫只处理未登录访问受保护页面的情况）
  - 登录成功后使用 `navigate('/employee', { replace: true })` 替换历史记录，避免用户按返回键回到登录页
  - Mock 数据中的 token 可以使用简单的时间戳生成（如 `'mock-token-' + Date.now()`），无需真实 JWT

---

### T-006: B00 后端基础设施脚手架

- **经验**：
  - pycore 依赖 loguru，必须在 backend/requirements.txt 中添加 `loguru>=0.7.0`
  - uv 管理的 Python 环境需要创建项目内虚拟环境 `.venv` 才能安装依赖
  - pydantic-settings 的 BaseSettings 可以通过 `model_config` 的 `env_file` 参数从 .env 文件读取配置
  - 需要显式设置 .env 文件的绝对路径（使用 `Path(__file__).parent.parent.parent / ".env"`），避免在不同执行路径下找不到配置文件
  - pycore 通过 PYTHONPATH 引入，执行命令时需要设置 `PYTHONPATH=..`（从 backend/ 目录执行时）
  - Windows PowerShell 设置环境变量语法：`$env:PYTHONPATH=".."`
  - pyproject.toml 的 mypy exclude 配置需要排除 pycore 目录，避免框架代码的类型检查错误干扰业务代码验收
  - pydantic-settings 实例化时的类型检查错误可以使用 `# type: ignore[call-arg]` 注释忽略
  - pycore APIServer 已内置 /health 端点，无需额外实现
- **避坑**：
  - 不要使用系统 Python 安装依赖，必须创建虚拟环境
  - 运行 pytest、mypy、ruff 等工具时必须从项目根目录执行，并设置正确的 PYTHONPATH
  - backend/src/core/config.py 使用 pydantic-settings，不是 pycore 的 ConfigManager（ConfigManager 只支持 TOML）
  - 质量门禁命令必须排除 pycore 目录：`mypy backend/src backend/tests`

---

### T-007: B01 数据库模型与初始化

- **经验**：
  - SQLAlchemy ORM 模型中不能使用 `metadata` 作为字段名，因为它与 DeclarativeBase.metadata 冲突；应改用 `meta_data` 并通过 `mapped_column("metadata", ...)` 指定数据库列名
  - SQLite 相对路径（如 `sqlite:///./data/app.db`）需要去掉开头的 `./` 后再拼接项目根目录，否则会解析为系统根目录
  - Windows 控制台不支持 Unicode emoji 字符（✓、❌等），脚本输出应使用 ASCII 字符（如 `[OK]`、`[ERROR]`）
  - bcrypt 需要单独安装（`pip install bcrypt`），不在基础依赖中
  - ruff 的 `--unsafe-fixes` 选项可以自动修复 `str, enum.Enum` → `enum.StrEnum` 等不安全的升级
  - mypy 必须从 backend/ 目录内执行（`cd backend && mypy src tests`），才能正确应用 pyproject.toml 中的 `exclude = ["pycore/"]` 配置
  - 数据库初始化脚本需要使用 `PYTHONPATH=..` 从 backend/ 目录执行，确保 `src.*` 导入路径可用
- **避坑**：
  - 枚举类型在 SQLAlchemy 中必须设置 `native_enum=False`，避免 SQLite 不支持原生枚举类型导致错误
  - JSON 字段使用 `dict | None` 类型注解，不要用 `Optional[dict]`（ruff UP045）
  - 外键必须指定 `ondelete` 行为（`CASCADE` 或 `SET NULL`），避免删除主表记录时出现约束错误
  - 密码字段使用 bcrypt 哈希，调用 `bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")` 生成并存储为字符串

---

### T-008: B02 JWT 认证模块

- **经验**：
  - python-jose 库要求 JWT 的 `sub` 字段必须是字符串类型，传入整数会抛出 `Subject must be a string.` 错误
  - 创建 token 时需要将用户 ID 转换为字符串：`create_access_token(data={"sub": str(user.id)})`
  - 验证 token 时需要将 sub 从字符串转换回整数：`user_id = int(payload.get("sub"))`
  - FastAPI 的 HTTPBearer 在没有提供认证头时返回 401 状态码，不是 403
  - httpx AsyncClient 在新版本中需要使用 `ASGITransport` 来传递 ASGI app：`AsyncClient(transport=ASGITransport(app=app))`
  - 测试中需要正确覆盖数据库依赖，确保测试使用独立的内存数据库
  - pytest fixture 的类型注解需要匹配实际返回类型，async generator 需要正确声明
- **避坑**：
  - 不要在 JWT payload 中使用整数类型的 sub，必须是字符串
  - ruff B904 规则要求在 except 块中使用 `raise ... from e` 保留异常链
  - 测试数据库与运行时数据库必须完全隔离，不能共享连接
  - 移除调试 print 语句before 提交代码

---

### T-009: 用户登录认证功能闭环

- **经验**：
  - `useAuthStore.loadAuth()` 从同步改为异步函数，在有 token 时调用 `authService.getMe()` 验证并刷新用户信息
  - 如果 token 验证失败（401 或其他错误），必须清除 localStorage 中的 token 和 user，避免前端与后端状态不一致
  - `AppShell.handleLogout` 需要先调用 `authService.logout()` 通知后端，再调用 `clearAuth()` 清除本地状态
  - 登录错误处理需要区分后端返回的错误码（code 1001 = 用户名或密码错误），通过 `error.response?.data?.code` 获取
  - ESLint 禁止使用 `any` 类型，需要用 `unknown` 类型配合类型保护（type guard）来处理错误对象
  - `VITE_USE_MOCK=false` 时，前端会通过 Vite 代理请求真实后端 API，无需修改 axios baseURL
- **避坑**：
  - 不要在 catch 块中直接使用 `error: any`，应使用 `error: unknown` 并进行类型检查
  - 登录页的种子账号（zhangsan/password123）应与后端数据库一致，避免验收时因账号不匹配导致失败
  - Zustand store 的异步函数（如 `loadAuth`）返回类型必须是 `Promise<void>`，不能是 `void`
  - 修改 .env 文件后必须重启 Vite 开发服务器才能生效
  - **使用 `api` 实例（`baseURL=/api`）时，路径必须以 `/auth/*`、`/conversations/*` 等形式书写，禁止再写 `/api/` 前缀**（否则会请求 `/api/api/...` 导致 404）

---

### Bugfix: 发送消息后无 AI 回复

- **触发**：点击发送后按钮转圈，界面无回复
- **根因**：`reload()` 用无 messages 的列表覆盖 state；axios 10s 超时短于 RAG 耗时
- **修复**：send 后用返回的会话详情更新 state；timeout 120s；4xx 不重试
- **避坑**：integration 任务 list/detail 分离时，发送后必须用 detail 或 send 响应更新 messages

---

### Bugfix: 发送无气泡、需刷新才见历史

- **触发**：发送时仅按钮转圈；用户消息不即时出现；历史消息需刷新页面再点会话才显示
- **根因**：无乐观 UI，等 RAG 完成才渲染；首屏/`activeId` 仅 `list()` 不含 messages，未自动 `get(id)`
- **修复**：乐观追加用户气泡 + `pending` 助手加载气泡；首屏/切换会话/`reload` 后 `loadConversationDetail`
- **避坑**：聊天页 list/detail 分离时，进入会话必须拉详情；长耗时接口必须即时反馈（乐观 UI + 加载占位）
- **超时≠未发送**：axios 超时是浏览器放弃等响应，后端 RAG 可能仍在跑且已入库；失败回滚前应先 `get(id)` 或轮询确认
- **修改 `api.ts` 超时后必须重启 Vite**，否则仍走旧 bundle 的 10s 超时

---

### Bugfix: 无法发起会话（API 路径重复 /api）

- **触发**：员工端点击「+ 新对话」失败，无法加载会话列表
- **根因**：`conversationService` 使用 `/api/conversations`，与 axios `baseURL=/api` 拼接为 `/api/api/conversations`
- **修复**：改为 `/conversations`、`/conversations/{id}`、`/conversations/{id}/messages`
- **避坑规则**：所有走 `services/api.ts` 的 service 必须与 `authService` 路径风格一致；Tester 在 `VITE_USE_MOCK=false` 下必须验收新建会话

---

### T-010: 知识库上传入库与删除闭环

- **经验**：
  - DashScope Embedding API 端点为 `https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding`，返回格式为 `{"output": {"embeddings": [{"embedding": [float...]}]}}`
  - LLM 调用使用百炼兼容 OpenAI 端点 `{LLM_BASE_URL}/chat/completions`，返回格式与 OpenAI 一致
  - 向量数据需要使用 `struct.pack` 将 float 数组打包为 bytes 存储在 SQLite BLOB 字段中
  - 文件上传使用 FastAPI 的 `UploadFile` 和 `File(...)`，前端使用 `FormData` 传输
  - 异步入库使用 `asyncio.create_task` + **独立 DB session**（禁止复用请求 session）
  - 四库顺序入库（同一 session 内禁止 `asyncio.gather` 并行写 SQLite）
  - Embedding **必须批量调用**（`input.texts` 一次传多段，每批 ≤25），禁止逐 chunk 单条请求
  - DashScope/LLM HTTP 调用必须带 **重试**（至少 3 次）与 `_format_error` 可读错误信息
  - 前端轮询通过 `setInterval` 每 2.5 秒刷新列表，检测 processing 状态变化
  - Repository 层的 delete 操作依赖外键 `CASCADE` 自动删除关联数据
- **避坑**：
  - httpx 必须显式设置 `trust_env=False`，避免继承系统代理和环境变量
  - `httpx.ConnectError` 的 `str(e)` 可能为空，写入 `error_message` 前必须用 `_format_error` 包装
  - DashScope `text-embedding-v3` 同步接口 **`input.texts` 单次最多 10 条**，批量 Embedding 不得超过 10
  - SQLite 启用 WAL + busy_timeout；异步入库不得与上传请求共用 session
  - FastAPI 路由参数验证使用 `Query(ge=1)` 而不是 `Field(ge=1)`
  - 上传文件路径必须使用 `Path.mkdir(parents=True, exist_ok=True)` 确保目录存在
  - 前端 FormData 需要设置 `Content-Type: multipart/form-data` 头
  - 测试中需要使用内存数据库 `sqlite+aiosqlite:///:memory:` 避免污染真实数据
  - LLM 返回的 JSON 可能包含 markdown 代码块，需要提取 `[` 到 `]` 之间的内容

---

### Bugfix: 知识库入库全部失败（ConnectError）

- **触发**：上传 `.md` 后四库均失败，`error_message` 为空
- **根因**：逐 chunk 单条 Embedding + 无 HTTP 重试 → `httpx.ConnectError('')`；异常信息未格式化
- **已有经验回查**：T-010 有 API 端点说明，但未禁止逐条 Embedding
- **为什么仍然犯错**：经验未写成可执行的「批量 + 重试 + 错误格式化」规则
- **修复**：批量 Embedding、3 次重试、`_format_error()`、QA 数取实际入库条数
- **避坑规则**：Developer 实现 kb_ingest 时必须批量 Embedding；Tester 验收失败记录 `error_message` 非空

---

### Bugfix: 转人工 transfer 404

- **触发**：POST `/api/conversations/{id}/transfer` 404
- **根因**：8099 上 uvicorn 为旧进程，OpenAPI 无 transfer 路由（后端代码已更新但未重启）
- **验证**：`openapi.json` 是否含 `/api/conversations/{conversation_id}/transfer`
- **避坑**：新增后端路由后必须重启后端；用 `scripts/start-backend.ps1` 或 `--reload` 启动

---

### 本地启动：双窗口 + 虚拟环境 Python

- **现象**：只跑后端脚本后浏览器无页面；或 `python -m uvicorn` 一闪而过
- **原因**：前端需单独窗口 `npm run dev`；Windows 裸 `python` 常为商店占位符
- **做法**：见 `docs/startup.md`；后端用 `Projects_Repo/1/.venv/Scripts/python.exe`；前端默认 `http://127.0.0.1:5199`
- **避坑**：要求用户重启时，必须同时给出**后端窗口 + 前端窗口**完整命令，或指向 `scripts/start-*.ps1`

---

### Bugfix: 员工端无会话发送无响应

- **触发**：员工端点击发送无任何反应（无气泡、无提示）
- **根因**：`activeId` 为空时 `handleSend` 静默 return；WS 合并误删乐观 loading 气泡
- **已有经验回查**：有（发送无气泡），但未覆盖空会话静默 return
- **为什么仍然犯错**：空态与 WS 合并是后续增量逻辑，未纳入发送 UX 验收
- **修复**：无会话时发送自动 create；列表加载失败提示；`mergeWsMessage` 保留 loading 气泡
- **避坑**：`handleSend` 禁止静默 return；WS 合并不得 `filter(id>0)` 一刀切清除乐观 UI

---

### RAG 向量相似度分档

- **经验**：以向量 Top1 余弦相似度分档：<0.75 未命中无引用；[0.75,0.85) 返回答案并 `match_label=相似问题`；≥0.85 高置信直答
- **避坑**：分档只看向量相似度，不用 rerank 分数替代；前端用 `metadata.match_label` 展示标签

---

### T-018: 全系统 E2E 与启动文档

- **经验**：`docs/startup.md` 须含环境要求、双窗口启动、开发/验收端口（5199/8099 vs 5175/8003）、E2E 路径与测试账号
- **避坑**：pytest 各文件勿各自 `override get_db` 与独立 engine，统一用 `tests/conftest.py`；测试版 `get_db` 须在 yield 后 `commit` 与生产一致
- **验收**：`pytest tests` 40/40 + `npm run build` + 按 startup.md 全链路手动走通

---

### T-017: WebSocket 实时推送

- **经验**：`WS /ws/messages?token=` 按 `user_id` 推送；Vite `/ws` 代理须 `ws: true`
- **避坑**：新增 WS 路由后须重启后端；前端用相对路径 `ws://${location.host}/ws/messages`，勿硬编码 8099
- **事件**：`new_message`、`ticket_status_changed`、`ticket_created` 在 commit 后广播

---

### T-016: 工单归类与结束

- **经验**：`PATCH /tickets/{id}` 支持 `category` 或 `status=completed`；结束工单须同步 `conversation.status=completed`
- **避坑**：结束后员工端 `POST messages` 返回 2002；坐席端输入区随 `ticket.status` 只读

---

### T-015: 坐席回复与智能回复

- **经验**：`POST /tickets/{id}/messages` 写入 `role=agent`；`POST /tickets/{id}/suggest` 先跑 RAG 再 LLM 生成 3 条候选
- **避坑**：智能回复只填输入框，禁止自动发送；仅 `processing` 且接单坐席可操作

---

### T-014: 坐席工单列表与接单

- **经验**：列表 API 不含 `messages`，坐席端选中工单须 `GET /tickets/{id}` 拉详情
- **接单**：`POST /tickets/{id}/accept` 同时更新 `ticket.status=processing` 与 `conversation.status=processing`
- **避坑**：`ticketService` 路径用 `/tickets`，勿加 `/api` 前缀

---

### T-013: 转人工闭环

- **经验**：`POST /conversations/{id}/transfer` 创建 `tickets` 记录并将 `conversations.status` 置为 `queuing`；`conversation_id` 在 tickets 表唯一
- **避坑**：已完成或已在排队/处理中的会话应返回 400；前端转人工按钮仅在 `status=ai_chat` 时可点

---

### Bugfix: 知识库 Embedding 400 Bad Request

- **触发**：大文档入库失败，错误为 Embedding API 400
- **根因**：`EMBEDDING_BATCH_SIZE=25` 超过 DashScope 单次 10 条限制
- **修复**：批量上限改为 10；切块强制切分超长段落；400 响应体写入 `error_message`
- **避坑**：对接 DashScope Embedding 必须核对官方 batch/ token 限制，不能凭经验设 25

---

### Bugfix: 知识库「查看错误」只显示感叹号

- **触发**：失败记录点「查看错误」只有感叹号、无文字
- **根因**：`list_files` 未返回 `error_message`；前端 `message.info('')` 空 Toast
- **修复**：列表 API 带 `error_message`；改用 `Modal.error` + detail 兜底 + 默认说明文案
- **避坑**：list/detail 字段应对齐；错误展示禁止用空 `message.info`；失败态必须可读

---

### T-011: 会话管理功能闭环

- **经验**：
  - SQLAlchemy relationship 需要在两端模型都定义，`Conversation` 添加 `messages` 关系，`Message` 添加 `conversation` 关系
  - Repository 层使用 `selectinload()` 预加载关联数据，避免 N+1 查询
  - 前端列表 API 返回简化的会话对象（不含 messages），切换会话时按需加载完整详情
  - HTTPBearer 在缺少认证头时返回 401 而不是 403
  - PowerShell 不支持 `&&` 语法，需使用 `;` 或 `working_directory` 参数
  - 后端、前端和测试代码均已实现，通过 ruff、pytest、type-check、lint、build 全部质量门禁
  - 分页查询通过 `order_by(Conversation.updated_at.desc())` 按更新时间倒序排列
  - 前端员工端已完成只读状态实现（`status === 'completed'` 时禁用输入区）
- **避坑**：
  - 测试 unauthorized 场景时，预期状态码应为 401（HTTPBearer 行为）
  - 从 `backend/` 目录运行 mypy 才能正确应用 `pyproject.toml` 中的 `exclude` 配置
  - 前端 conversationService 在真实 API 模式下，list 返回简化对象需要添加空 messages 数组以符合类型定义
  - 切换会话时如果 messages 为空才加载详情，避免重复请求
  - mypy 检查可能报告其他模块的 pre-existing 错误，需要区分是否为本任务引入

---

### T-012: AI 问答与多轮对话 RAG 闭环

- **经验**：
  - RAG pipeline 实现了完整的 6 步链路：Query 改写 → QA 直答（阈值 0.8）→ 意图识别 → 槽位填充 → RRF 混合检索 → Rerank（可降级）→ 生成
  - QA 直答使用余弦相似度计算，阈值设置为 0.8，匹配成功直接返回答案，避免进入检索链路
  - 意图识别通过 LLM 返回 JSON，`vague_query` 触发反问，`clear_query` 继续检索
  - 槽位填充结合短期记忆（最近 3 轮对话）和长期记忆（user_profile 表的 department、common_topics、preferences）
  - RRF 混合检索使用 k=60，融合向量检索和关键词检索的结果
  - Rerank 调用百炼 API，失败时降级返回原顺序，保证系统可用性
  - 余弦相似度计算使用 `struct.unpack` 解包 BLOB 字段中的向量数据
  - ConversationService.send_message 需要检查 message_repo、profile_repo、rag_pipeline 是否为 None，避免 mypy union-attr 错误
  - json.loads 返回 Any 类型，需要显式声明 `intent: dict` 来满足类型检查
  - 前端 conversationService.sendMessage 调用真实 API 后，通过 `this.get(conversationId)` 重新加载会话详情，确保消息列表更新
  - ChatBubble 组件已支持 `metadata.citations` 自动展示引用来源卡片
  - 长期记忆更新使用简单规则提取（关键词匹配部门和话题），production 可替换为 LLM 提取
- **避坑**：
  - QA 直答匹配前必须检查 `best_qa is not None`，避免 mypy union-attr 错误
  - dict 的 sort key lambda 中使用 `float(x["similarity"])` 确保类型一致，添加 `# type: ignore[arg-type]` 避免 mypy 报错
  - RagPipeline 初始化需要传入 AsyncSession，在路由中每次请求时创建新实例
  - POST /api/conversations/{id}/messages 路由中需要 `await db.commit()` 提交事务，确保数据持久化
  - 已完成会话（status=completed）发送消息应返回 code 2002，HTTP 400 错误
  - 短期记忆只保留 user 和 assistant 角色的消息，过滤掉 system 和 agent 消息避免干扰
  - 前端 Message 类型的 metadata 字段已包含 citations 数组，不需要额外类型定义
