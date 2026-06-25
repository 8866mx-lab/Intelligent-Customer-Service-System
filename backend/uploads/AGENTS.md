1. 项目说明

本项目是一个 AiPPT Agent Demo 项目。

项目目标不是做一个静态页面，而是做成一个可以给面试官真实体验的 AI SaaS Demo。

最终效果是：

面试官可以打开一个线上网址
使用测试账号登录
进入工作台
新建会话
输入 PPT 生成需求
看到 Agent 执行过程
查看生成结果
刷新页面后，历史会话和生成记录仍然存在
2. 当前阶段目标

当前项目的第一阶段目标是：

支持线上部署
支持测试账号登录
支持会话持久化
支持消息持久化
支持 Agent 任务状态保存
支持 PPT / HTML 作品保存
支持部署到 Vercel
数据库使用 Supabase PostgreSQL

第一阶段不要追求完整商业化系统，优先保证面试 Demo 可以跑通。

3. 技术栈

当前项目预期技术栈：

前端：Next.js / React / TypeScript
样式：Tailwind CSS
后端：Next.js API Routes
数据库：Supabase PostgreSQL
ORM：Prisma
部署：Vercel
AI 模型：OpenAI-compatible API，通过环境变量配置

如果当前项目实际实现和这里不一致，请先分析现有结构，不要直接大规模重构。

4. 重要目录

修改代码前，请优先检查这些目录：

src/app/：页面和路由
src/app/api/：后端接口
src/components/：前端组件
src/lib/agent/：Agent 编排、Planner、Executor、Reporter、Memory
src/lib/llm/：大模型调用封装
src/lib/rag/：RAG 检索相关逻辑
src/lib/html/：HTML 幻灯片生成和渲染
src/lib/pptx/：PPTX 导出逻辑
src/lib/repository.ts：当前数据存储逻辑
src/lib/db.ts：当前数据库访问逻辑
data/：本地 mock 数据或运行时数据，不要当作正式生产数据库
5. 开发原则

开发时请遵守：

不要一上来大规模重构。
每次只解决一个明确模块。
优先做最小可用改造。
不要随意删除已有功能。
不要把当前 UI 改成通用模板。
修改前先分析相关文件。
修改后说明：
改了哪些文件
为什么这么改
如何本地验证
是否需要配置环境变量
是否有风险
所有改动都要服务于“面试可演示 Demo”。
6. 安全规则

绝对不要把真实密钥写进代码仓库。

不能提交：

.env
.env.local
.env.production
OpenAI API Key
数据库密码
Supabase service role key
SSH 私钥
本地数据库文件
本地运行时用户数据

可以提交：

.env.example
config/llm.example.json

.env.example 只能写变量名，不能写真正的密钥。

7. Git 规则

提交信息统一使用英文，避免 Windows 终端中文乱码。

推荐提交信息：

initial commit
add agents instructions
add supabase database schema
add demo login flow
persist chat messages
add agent task states
prepare vercel deployment

不要使用中文 commit message。

8. 包管理和启动命令

当前项目存在 package-lock.json，因此优先使用 npm。

常用命令：

npm install
npm run dev
npm run build

不要随意切换成 pnpm 或 yarn。

如果需要切换包管理器，必须先说明原因。

9. 数据库改造目标

项目后续需要从本地 JSON / 本地数据库，逐步迁移到 Supabase PostgreSQL。

优先使用 Prisma 管理数据库模型。

建议数据库模型包括：

User：用户
Conversation：会话
Message：消息
Task：Agent 执行任务
Project：PPT / HTML 作品
CreditLog：积分记录
Feedback：点赞点踩反馈

需要维护：

prisma/schema.prisma
migration 文件
.env.example

.env.example 至少包含：

DATABASE_URL=
DIRECT_URL=
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
OPENAI_API_KEY=

注意：不要把真实值写进 .env.example。

10. 登录目标

项目需要支持面试 Demo 登录。

要求：

支持测试账号登录。
未登录用户访问工作台时，跳转登录页。
登录后进入工作台。
刷新页面后登录状态不丢失。
支持退出登录。

登录可以使用 Supabase Auth，也可以先使用简单 Demo 登录方案，但不要把明文密码或敏感信息暴露到前端。

11. 会话和消息持久化目标

项目需要保存：

会话列表
会话标题
用户消息
助手回复
消息时间
关联的 Agent 任务 ID

要求：

用户新建会话后写入数据库。
用户发送消息后保存 user message。
Agent 回复后保存 assistant message。
左侧历史会话从数据库读取。
刷新页面后历史记录不能丢失。
12. Agent 任务状态目标

项目需要保存 Agent 任务执行状态。

最小状态包括：

pending
planning
clarifying
retrieving
generating
rendering
completed
failed

要求：

每次 Agent 执行时创建 Task。
执行过程中更新 Task 状态。
失败时记录 failed 和失败原因。
前端可以展示任务进度。
普通用户界面不要展示过多 debug 信息。
13. PPT / HTML 作品保存目标

生成的 PPT / HTML 作品需要保存。

最小字段包括：

作品 ID
用户 ID
会话 ID
标题
状态
页面数据
HTML 内容或存储引用
导出地址
创建时间
更新时间

要求：

作品列表可以展示历史作品。
作品详情页可以打开历史生成结果。
刷新页面后作品仍然存在。
不要只依赖本地 JSON 文件保存作品。
14. UI 要求

本项目是 AiPPT Agent Demo，需要像真实 AI 产品。

要求：

保持现有 UI 风格。
不要随意重做页面。
用户应该能清楚看到工作台、会话、Agent 执行过程和生成结果。
Agent 执行过程应该是产品化进度展示，不是底层 debug 日志。
普通用户界面不要展示内部阈值、相似度、覆盖率等 debug 信息。
如果需要 debug 面板，应放在独立调试页面或管理功能中。
15. 不要做的事

不要：

不经确认就重构整个项目。
删除已有 Agent 模块。
把 UI 改成无关模板。
提交密钥。
提交本地数据库文件。
提交本地运行时数据。
一次性混合处理登录、数据库、部署、Agent、PPT 导出等多个大模块。
隐瞒构建失败或功能未完成。
16. 推荐工作方式

每次任务请按这个流程：

先分析相关文件。
说明当前实现。
说明问题。
给出最小改造方案。
再修改代码。
修改后说明改了哪些文件。
给出本地验证方法。
给出下一步建议。

如果任务很大，请主动拆分成多个小任务。

17. 面试 Demo 完成标准

项目达到以下状态，可以认为初步 Demo-ready：

项目可以部署到 Vercel。
面试官可以使用测试账号登录。
面试官可以创建会话。
消息刷新后不丢失。
Agent 执行状态可见。
至少有一个 PPT / HTML 作品可以生成或展示。
页面没有明显断链。
GitHub 仓库没有泄露密钥。
README 说明了项目介绍、本地启动、环境变量和部署方式。
面试时能用 3 分钟讲清楚产品亮点。