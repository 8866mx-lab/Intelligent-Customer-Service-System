# 智能客服系统 — 原型交接说明

> 本目录为 B2 阶段设计验证用 HTML 原型，**非生产前端源码**。

## 快速打开

在浏览器中打开 `index.html` 查看总览，或直接进入各页面：

| 文件 | 页面 |
|------|------|
| `01-login.html` | P01 登录页 |
| `02-employee.html` | P02 员工端 |
| `03-agent.html` | P03 坐席端 |
| `04-knowledge.html` | P04 知识库 |

推荐演示路径：登录 → 员工端提问 → 转人工 → 坐席端接单 → 知识库上传

## 页面清单

| 页面 | 布局 | 目标视口 |
|------|------|----------|
| P01 登录 | 居中卡片 400px | 1440×900 |
| P02 员工端 | 左 280px 会话列表 + 右对话区 | 1440×900 |
| P03 坐席端 | 左 320px 工单分组 + 右对话操作区 | 1440×900 |
| P04 知识库 | 上传区 + 文件表格，单栏全宽 | 1440×900 |

全局 Shell：P02/P03/P04 共用顶部导航（员工端 / 坐席端 / 知识库 Tab + 用户下拉）

## 关键组件清单

| 组件 | 生产实现建议 |
|------|-------------|
| 顶部导航 Shell | Ant Design Layout.Header + Menu |
| 会话/工单列表 | Ant Design List，选中态左边框 |
| 对话气泡 | 自定义组件，三色区分 user/ai/agent |
| 引用来源卡片 | AI 气泡内嵌 Card，**必须生产实现**（签名质感锚点） |
| 智能回复候选 | Ant Design Popover / 自定义面板 |
| 文件上传 | Ant Design Upload.Dragger，限 .md |
| 文件表格 | Ant Design Table |
| 状态 Tag | Ant Design Tag |

## 交互状态（原型已演示）

| 状态 | 页面 | 表现 |
|------|------|------|
| 登录提交 | P01 | 跳转员工端 |
| 切换历史会话 | P02 | 已完成会话输入区变只读提示 |
| 新建对话 | P02 | 清空对话区 |
| 发送消息 | P02 | 追加用户气泡 + AI 占位回复 |
| 转人工 | P02 | 确认后跳转坐席端 |
| 接单 | P03 | 状态变处理中，显示操作面板 |
| 智能回复 | P03 | 展开 3 条候选，点击填入输入框 |
| 发送回复 | P03 | 追加坐席气泡 |
| 结束工单 | P03 | 输入区变只读 |
| 模拟上传 | P04 | 新增行 → 2 秒后变已完成 |
| 入库详情 | P04 | alert 展示四库状态 |

## Mock 数据结构

```json
{
  "conversation": {
    "id": 1,
    "title": "请假流程咨询",
    "status": "ai_chat | queuing | processing | completed",
    "messages": [
      { "role": "user|assistant|agent", "content": "...", "metadata": { "citations": [...] } }
    ]
  },
  "ticket": {
    "id": 1024,
    "conversation_id": 1,
    "user_name": "李四",
    "category": "it|hr|finance|admin|other",
    "status": "pending|processing|completed"
  },
  "kb_file": {
    "filename": "员工手册.md",
    "chunk_count": 42,
    "qa_count": 15,
    "stores": { "vector": "completed", "keyword": "completed", "metadata": "completed", "qa": "completed" },
    "status": "pending|processing|completed|failed"
  }
}
```

## 需要真实 API 的位置

| 页面 | 接口 | 说明 |
|------|------|------|
| P01 | POST /api/auth/login | 账号密码登录 |
| P02 | POST /api/conversations | 新建会话 |
| P02 | GET /api/conversations | 历史会话列表 |
| P02 | POST /api/conversations/:id/messages | 发送消息（触发 RAG 链路） |
| P02 | POST /api/conversations/:id/transfer | 转人工 |
| P03 | GET /api/tickets | 工单列表 |
| P03 | POST /api/tickets/:id/accept | 接单 |
| P03 | POST /api/tickets/:id/messages | 坐席回复 |
| P03 | POST /api/tickets/:id/suggest | 智能回复候选 |
| P03 | PATCH /api/tickets/:id | 归类 / 结束工单 |
| P04 | POST /api/kb/upload | 上传 .md |
| P04 | GET /api/kb/files | 文件列表 |
| P04 | GET /api/kb/files/:id | 入库详情 |
| P04 | DELETE /api/kb/files/:id | 删除文件 |
| 全局 | WebSocket /ws | 员工端 ↔ 坐席端实时消息 |

## 生产必须实现的视觉效果

- AI 回答中的**引用来源卡片**（文档名 + 片段预览 + 查看原文）
- 用户/AI/坐席三色消息气泡区分
- 工单/会话状态 Tag 色彩体系
- 顶部导航 Shell 统一布局

## 仅为原型展示的效果

- 「正在检索知识库…」固定文案（生产需 SSE/流式输出）
- 上传 2 秒自动完成（生产需异步任务 + 轮询/WebSocket）
- alert/confirm 弹窗（生产需 Ant Design Modal/Message）
- 智能回复候选用静态文本（生产走 RAG API）

## 设计参考

- Design Spec：`.sdd/tmp/ui-design-spec.md`（B2 完成后可删除）
- 视觉调研：`.sdd/tmp/visual-research.md`
- PRD：`docs/PRD.md`
