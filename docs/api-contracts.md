# 接口契约

> 前端 Mock 和后端实现的唯一对齐依据。任何变更必须同步更新本文件。

## 通用约定

### 统一响应格式

成功：

```json
{"code": 200, "message": "success", "data": { }}
```

错误：

```json
{"code": 1001, "message": "错误描述", "data": null}
```

分页：

```json
{"code": 200, "message": "success", "data": {"items": [], "total": 100, "page": 1, "page_size": 20}}
```

### HTTP 状态码

| 状态码 | 含义 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 认证

除 `POST /api/auth/login` 和 `GET /health` 外，所有 REST 接口需在 Header 携带：

```text
Authorization: Bearer <access_token>
```

### 枚举值

**会话状态 conversation.status**：`ai_chat` | `queuing` | `processing` | `completed`

**工单状态 ticket.status**：`pending` | `processing` | `completed`

**工单分类 ticket.category**：`it` | `hr` | `finance` | `admin` | `other`

**消息角色 message.role**：`user` | `assistant` | `agent` | `system`

**知识库文件状态 kb_file.status**：`pending` | `processing` | `completed` | `failed`

**四库入库状态 store_status**：`pending` | `processing` | `completed` | `failed`

---

## 接口清单

### GET /health

**说明**：健康检查，无需认证。

**响应（成功 200）：**

```json
{"code": 200, "message": "success", "data": {"status": "ok"}}
```

---

### POST /api/auth/login

**说明**：账号密码登录。

**请求体：**

```json
{
  "username": "zhangsan",
  "password": "password123"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 1,
      "username": "zhangsan"
    }
  }
}
```

**响应（失败 401）：**

```json
{"code": 1001, "message": "用户名或密码错误", "data": null}
```

---

### POST /api/auth/logout

**说明**：退出登录（客户端清除 Token，服务端可选黑名单）。

**请求体：** 无

**响应（成功 200）：**

```json
{"code": 200, "message": "success", "data": null}
```

---

### GET /api/auth/me

**说明**：获取当前登录用户信息。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan"
  }
}
```

**响应（失败 401）：**

```json
{"code": 1002, "message": "Token 已过期或无效", "data": null}
```

---

### GET /api/conversations

**说明**：获取当前用户的历史会话列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 50 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "请假流程咨询",
        "status": "ai_chat",
        "created_at": "2026-06-06T14:32:00+08:00",
        "updated_at": "2026-06-06T14:35:00+08:00"
      },
      {
        "id": 2,
        "title": "VPN 无法连接",
        "status": "queuing",
        "created_at": "2026-06-06T11:20:00+08:00",
        "updated_at": "2026-06-06T11:25:00+08:00"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 50
  }
}
```

---

### POST /api/conversations

**说明**：新建会话。

**请求体：**

```json
{
  "title": "新对话"
}
```

`title` 可选，默认「新对话」。

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 3,
    "title": "新对话",
    "status": "ai_chat",
    "created_at": "2026-06-06T15:00:00+08:00",
    "updated_at": "2026-06-06T15:00:00+08:00"
  }
}
```

---

### GET /api/conversations/{conversation_id}

**说明**：获取会话详情及消息列表。

**路径参数：** `conversation_id` (int)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "请假流程咨询",
    "status": "ai_chat",
    "created_at": "2026-06-06T14:32:00+08:00",
    "updated_at": "2026-06-06T14:35:00+08:00",
    "messages": [
      {
        "id": 1,
        "role": "assistant",
        "content": "您好，我是企业内部智能助手，有什么可以帮您的？",
        "metadata": null,
        "created_at": "2026-06-06T14:32:01+08:00"
      },
      {
        "id": 2,
        "role": "user",
        "content": "请问公司的请假流程是什么？",
        "metadata": null,
        "created_at": "2026-06-06T14:32:30+08:00"
      },
      {
        "id": 3,
        "role": "assistant",
        "content": "根据《员工手册》规定，请假流程如下：\n1. 提前在 OA 系统提交请假申请\n2. 直属主管审批\n3. 人事部门备案",
        "metadata": {
          "response_type": "rag",
          "intent": "clear_query",
          "citations": [
            {
              "file_id": 1,
              "filename": "员工手册.md",
              "chunk_index": 12,
              "preview": "员工请假应提前通过 OA 系统提交申请，经直属主管审批后生效。年假须提前 3 个工作日申请…",
              "similarity": 0.92
            }
          ]
        },
        "created_at": "2026-06-06T14:32:35+08:00"
      }
    ]
  }
}
```

**响应（失败 404）：**

```json
{"code": 2001, "message": "会话不存在", "data": null}
```

---

### POST /api/conversations/{conversation_id}/messages

**说明**：发送用户消息，触发 RAG 链路并返回 AI 回复。

**路径参数：** `conversation_id` (int)

**请求体：**

```json
{
  "content": "请问公司的请假流程是什么？"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "user_message": {
      "id": 2,
      "role": "user",
      "content": "请问公司的请假流程是什么？",
      "metadata": null,
      "created_at": "2026-06-06T14:32:30+08:00"
    },
    "assistant_message": {
      "id": 3,
      "role": "assistant",
      "content": "根据《员工手册》规定，请假流程如下：\n1. 提前在 OA 系统提交请假申请\n2. 直属主管审批\n3. 人事部门备案",
      "metadata": {
        "response_type": "rag",
        "intent": "clear_query",
        "citations": [
          {
            "file_id": 1,
            "filename": "员工手册.md",
            "chunk_index": 12,
            "preview": "员工请假应提前通过 OA 系统提交申请…",
            "similarity": 0.92
          }
        ]
      },
      "created_at": "2026-06-06T14:32:35+08:00"
    }
  }
}
```

**metadata.response_type 取值：**

| 值 | 说明 |
|----|------|
| `qa_match` | QA 库直答（相似度 ≥ 0.8） |
| `clarify` | 意图模糊，反问 |
| `rag` | RAG 检索生成 |
| `mock` | Mock 降级（无 API Key 时） |

**响应（失败 400）：**

```json
{"code": 2002, "message": "会话已完成，不可发送消息", "data": null}
```

---

### POST /api/conversations/{conversation_id}/transfer

**说明**：转人工，创建工单并将会话置为排队中。

**路径参数：** `conversation_id` (int)

**请求体：** 无

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "conversation_id": 2,
    "conversation_status": "queuing",
    "ticket": {
      "id": 1024,
      "conversation_id": 2,
      "status": "pending",
      "created_at": "2026-06-06T11:25:00+08:00"
    }
  }
}
```

**响应（失败 400）：**

```json
{"code": 2002, "message": "会话已完成，不可转人工", "data": null}
```

---

### GET /api/tickets

**说明**：获取工单列表（坐席端）。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 筛选：`pending` / `processing` / `completed` |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 50 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1024,
        "conversation_id": 2,
        "user_id": 2,
        "user_name": "李四",
        "agent_id": null,
        "category": null,
        "status": "pending",
        "summary": "VPN 无法连接",
        "created_at": "2026-06-06T11:20:00+08:00",
        "updated_at": "2026-06-06T11:25:00+08:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 50
  }
}
```

---

### GET /api/tickets/{ticket_id}

**说明**：获取工单详情及完整对话历史。

**路径参数：** `ticket_id` (int)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1024,
    "conversation_id": 2,
    "user_id": 2,
    "user_name": "李四",
    "agent_id": 1,
    "agent_name": "张三",
    "category": "it",
    "status": "processing",
    "summary": "VPN 无法连接",
    "created_at": "2026-06-06T11:20:00+08:00",
    "updated_at": "2026-06-06T11:30:00+08:00",
    "messages": [
      {
        "id": 10,
        "role": "user",
        "content": "公司的 VPN 连不上了，提示认证失败",
        "metadata": null,
        "created_at": "2026-06-06T11:20:05+08:00"
      },
      {
        "id": 11,
        "role": "assistant",
        "content": "抱歉，未能找到 VPN 认证失败的具体方案，建议转接人工客服。",
        "metadata": {"response_type": "rag", "intent": "clear_query"},
        "created_at": "2026-06-06T11:20:15+08:00"
      },
      {
        "id": 12,
        "role": "system",
        "content": "已转人工",
        "metadata": null,
        "created_at": "2026-06-06T11:25:00+08:00"
      }
    ]
  }
}
```

**响应（失败 404）：**

```json
{"code": 3001, "message": "工单不存在", "data": null}
```

---

### POST /api/tickets/{ticket_id}/accept

**说明**：坐席接单。

**路径参数：** `ticket_id` (int)

**请求体：** 无

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1024,
    "status": "processing",
    "agent_id": 1,
    "conversation_status": "processing",
    "updated_at": "2026-06-06T11:30:00+08:00"
  }
}
```

**响应（失败 400）：**

```json
{"code": 3002, "message": "工单状态不允许接单", "data": null}
```

---

### POST /api/tickets/{ticket_id}/messages

**说明**：坐席发送人工回复。

**路径参数：** `ticket_id` (int)

**请求体：**

```json
{
  "content": "您好，VPN 认证失败通常是密码过期，请在 OA 重置密码后重试。"
}
```

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 13,
    "role": "agent",
    "content": "您好，VPN 认证失败通常是密码过期，请在 OA 重置密码后重试。",
    "metadata": null,
    "created_at": "2026-06-06T11:31:00+08:00"
  }
}
```

---

### POST /api/tickets/{ticket_id}/suggest

**说明**：智能回复，生成 3 条候选建议（走 RAG 链路）。

**路径参数：** `ticket_id` (int)

**请求体：** 无（基于工单对话上下文）

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "suggestions": [
      {
        "index": 1,
        "content": "您好，VPN 认证失败通常是密码过期导致，请尝试在 OA 系统重置密码后重新连接。"
      },
      {
        "index": 2,
        "content": "请确认您使用的是公司分配的 VPN 客户端（版本 3.2+），旧版本可能导致认证失败。"
      },
      {
        "index": 3,
        "content": "如仍无法连接，请提供错误截图，我帮您进一步排查。也可拨打 IT 热线 8888。"
      }
    ]
  }
}
```

---

### PATCH /api/tickets/{ticket_id}

**说明**：更新工单（归类或结束）。

**路径参数：** `ticket_id` (int)

**请求体（归类）：**

```json
{
  "category": "it"
}
```

**请求体（结束工单）：**

```json
{
  "status": "completed"
}
```

**响应（成功 200，结束工单）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1024,
    "status": "completed",
    "category": "it",
    "conversation_status": "completed",
    "updated_at": "2026-06-06T11:45:00+08:00"
  }
}
```

**响应（失败 400）：**

```json
{"code": 3002, "message": "工单状态不允许此操作", "data": null}
```

---

### POST /api/kb/upload

**说明**：上传 .md 知识库文件并触发入库。

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | file | 是 | 仅支持 .md |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 5,
    "filename": "员工手册.md",
    "status": "processing",
    "created_at": "2026-06-06T14:30:00+08:00"
  }
}
```

**响应（失败 400）：**

```json
{"code": 4001, "message": "仅支持 .md 格式文件", "data": null}
```

---

### GET /api/kb/files

**说明**：知识库文件列表。

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页条数，默认 20 |

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "filename": "员工手册.md",
        "status": "completed",
        "chunk_count": 42,
        "qa_count": 15,
        "stores": {
          "vector": "completed",
          "keyword": "completed",
          "metadata": "completed",
          "qa": "completed"
        },
        "uploaded_by": 1,
        "created_at": "2026-06-06T14:30:00+08:00",
        "updated_at": "2026-06-06T14:31:00+08:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

---

### GET /api/kb/files/{file_id}

**说明**：知识库文件入库详情。

**路径参数：** `file_id` (int)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "filename": "员工手册.md",
    "status": "completed",
    "chunk_count": 42,
    "qa_count": 15,
    "stores": {
      "vector": "completed",
      "keyword": "completed",
      "metadata": "completed",
      "qa": "completed"
    },
    "error_message": null,
    "uploaded_by": 1,
    "created_at": "2026-06-06T14:30:00+08:00",
    "updated_at": "2026-06-06T14:31:00+08:00"
  }
}
```

**响应（失败 404）：**

```json
{"code": 404, "message": "文件不存在", "data": null}
```

---

### DELETE /api/kb/files/{file_id}

**说明**：删除知识库文件及四库索引数据。

**路径参数：** `file_id` (int)

**响应（成功 200）：**

```json
{"code": 200, "message": "success", "data": null}
```

---

### POST /api/kb/files/{file_id}/retry

**说明**：入库失败后重试。

**路径参数：** `file_id` (int)

**响应（成功 200）：**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 4,
    "filename": "行政管理制度.md",
    "status": "processing",
    "updated_at": "2026-06-06T16:00:00+08:00"
  }
}
```

---

## WebSocket

### WS /ws/messages

**说明**：实时消息推送（员工端 ↔ 坐席端）。

**连接：** `ws://<host>/ws/messages?token=<access_token>`

**服务端推送事件：**

```json
{
  "event": "new_message",
  "data": {
    "conversation_id": 2,
    "ticket_id": 1024,
    "message": {
      "id": 13,
      "role": "agent",
      "content": "您好，VPN 认证失败通常是密码过期…",
      "metadata": null,
      "created_at": "2026-06-06T11:31:00+08:00"
    }
  }
}
```

```json
{
  "event": "ticket_status_changed",
  "data": {
    "ticket_id": 1024,
    "status": "completed",
    "conversation_id": 2,
    "conversation_status": "completed"
  }
}
```

**事件类型：**

| event | 说明 |
|-------|------|
| `new_message` | 新消息（坐席回复或系统消息） |
| `ticket_status_changed` | 工单/会话状态变更 |
| `ticket_created` | 新工单创建（转人工） |

---

## 业务错误码汇总

| 错误码 | 说明 |
|--------|------|
| 1001 | 用户名或密码错误 |
| 1002 | Token 过期或无效 |
| 2001 | 会话不存在 |
| 2002 | 会话已完成，不可发送消息 |
| 3001 | 工单不存在 |
| 3002 | 工单状态不允许此操作 |
| 4001 | 文件格式不支持（仅 .md） |
| 4002 | 知识库入库失败 |
