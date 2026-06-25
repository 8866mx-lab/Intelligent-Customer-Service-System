# 测试报告：T-003 P02 员工端 Mock 实现

**测试时间**：2026-06-06
**Tester Agent ID**：tester-subagent

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 用户在员工端左侧看到按时间排列的历史会话列表，右侧为对话区域和底部输入框，布局与 docs/prototypes/02-employee.html 一致 | PASS | `EmployeePage.tsx` 左栏 `session-list` + 右栏 `chat-messages`/`chat-input-area`；按钮「+ 新对话」、placeholder「输入您的问题…」、操作「转人工」「发送」与原型一致 |
| 2 | 用户点击左侧某条未完成会话，右侧展示该会话 Mock 消息气泡（用户/AI/坐席三色区分），AI 回答内嵌引用来源卡片 | PASS | `ChatBubble.tsx` 按 role 区分样式；`mocks/conversations.ts` id=1 含 citations；`CitationCard.tsx` 渲染文档名+片段预览+「查看原文 →」 |
| 3 | 用户在输入框输入问题并点击发送，本页面对话区追加用户气泡和 AI 回复气泡 | PASS | `conversationService.sendMessage` → `appendUserMessage` 追加 user + assistant 气泡后 `reload()` 刷新 UI |
| 4 | 用户点击「新建会话」，对话区清空并展示新会话空白状态 | PASS | `handleNewSession` 调用 `conversationService.create()`，Mock 返回含 assistant 欢迎语的新会话并切换 activeId |
| 5 | 用户选择状态为已完成的会话时，底部输入区变为只读提示且无法发送消息 | PASS | `isReadOnly = active?.status === 'completed'`；只读文案「该会话已结束，不可继续发送消息」；`handleSend` 对 completed 拦截 |
| 6 | 用户点击「转人工」并确认后，本页面展示已进入排队/转人工的 Mock 状态提示 | PASS | `Modal.confirm` 文案与原型一致；`transferConversation` 将 status 设为 queuing 并追加 system 消息「已转人工，正在排队中…」 |

## technicalChecks 逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | cd frontend && npm run type-check 通过 | PASS | `tsc --noEmit` exit 0 |
| 2 | cd frontend && npm run lint 通过 | PASS | `eslint .` exit 0 |
| 3 | cd frontend && npm run build 通过 | PASS | `tsc -b && vite build` exit 0 |
| 4 | Mock 会话/消息数据结构符合 api-contracts.md conversations 与 messages 契约 | PASS | `types/conversation.ts` 与 `mocks/conversations.ts` 字段为契约子集（id/title/status/created_at/updated_at/messages/role/content/metadata/citations） |
| 5 | CitationCard 引用来源卡片已实现（文档名+片段预览），非纯文本占位 | PASS | `CitationCard.tsx` 独立组件，含 filename、preview、「查看原文 →」 |
| 6 | 固定高度列表项在浏览器中文字不被垂直截断（容器高度预留 ≥20% 缓冲） | PASS | `EmployeePage.css` `.session-meta { min-height: 24px }`；`.session-title` 单行 ellipsis 仅水平截断；tag 行高 20px 与原型 `.tag` 一致 |

## 代码质量检查

| 检查项 | 结果 | 说明 |
|--------|------|------|
| Mock 拦截 | PASS | `conversationService.ts` 在 `VITE_USE_MOCK=true` 时仅调用 `@/mocks/conversations`，无 axios 请求 |
| 密钥泄露 | PASS | 前端源码无真实 API Key |
| TODO/FIXME | PASS | 相关页面/组件无遗留标记 |

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | CitationCard 标题格式为「文件名 · 第 N 段」，原型为「📄 文件名 · 第 N 章」 | 员工端 | 可选优化文案对齐；当前使用 api-contracts chunk_index 字段，功能不受影响 |
