# 智能客服 — 本地启动说明

## 环境要求

| 项目 | 版本/说明 |
|------|-----------|
| 操作系统 | Windows 10+（本文以 PowerShell 为例） |
| Node.js | 18+（前端 `npm run dev` / `npm run build`） |
| Python | 3.11+，使用项目虚拟环境 `.venv` |
| 百炼 DashScope | 需配置 `DASHSCOPE_API_KEY`（RAG、智能回复、知识库入库） |

后端环境变量见 `backend/.env.example`，复制为 `backend/.env` 后填入 Key。**切勿将真实 API Key 提交到仓库。**

前端默认配置见 `frontend/.env`：

```env
VITE_API_BASE_URL=/api
VITE_USE_MOCK=false
VITE_BACKEND_PROXY_TARGET=http://localhost:8099
```

`VITE_USE_MOCK=false` 表示全链路走真实后端，不使用 Mock。

---

## 重要：需要两个 PowerShell 窗口

| 窗口 | 作用 | 关掉会怎样 |
|------|------|------------|
| **窗口 1** | 后端 API + WebSocket | 接口全部失败 |
| **窗口 2** | 前端页面 | **浏览器打不开页面** |

只执行后端命令、不启动前端，就会出现「看不到前端页面」。

---

## 一键脚本（推荐）

### 窗口 1 — 后端

```powershell
cd d:\zhinengkefu\SDD_V7_1_2\SDD_V7_1_2\Projects_Repo\1\scripts
.\start-backend.ps1
```

看到 `Uvicorn running on http://127.0.0.1:8099` 即成功。**不要关这个窗口。**

### 窗口 2 — 前端

**再开一个** PowerShell：

```powershell
cd d:\zhinengkefu\SDD_V7_1_2\SDD_V7_1_2\Projects_Repo\1\scripts
.\start-frontend.ps1
```

看到 `Local: http://127.0.0.1:5199/` 即成功。**不要关这个窗口。**

### 浏览器访问

```text
http://127.0.0.1:5199/login
```

测试账号：`zhangsan` / `password123`

---

## 端口说明

| 服务 | 开发端口 | 验收端口 | 说明 |
|------|----------|----------|------|
| 前端 | **5199** | **5175** | 开发默认 5199；验收环境可能使用 5175 |
| 后端 | **8099** | **8003** | API + WebSocket；Vite 将 `/api`、`/ws` 代理到此后端 |

若终端打印的端口与上表不同，**以终端实际输出为准**。

---

## 不要用裸 `python`

Windows 上的 `python` 可能是微软商店占位符，执行后立刻回到提示符、**没有真正启动服务**。

本项目请使用虚拟环境：

```text
Projects_Repo\1\.venv\Scripts\python.exe
```

`start-backend.ps1` 已自动使用该路径。

---

## 验证服务是否正常

```powershell
# 后端健康检查
curl http://127.0.0.1:8099/health

# 前端（应返回 HTML）
curl http://127.0.0.1:5199
```

`GET /health` 应返回 `{"code":200,"data":{"status":"ok"},...}`。

---

## 全链路 E2E 验收路径（MVP）

按以下顺序可覆盖 PRD 全部 24 项功能（F-01～F-04）：

1. **登录**（F-01）— `/login`，账号 `zhangsan` / `password123`
2. **知识库**（F-04）— `/knowledge` 上传 `.md` 文件，等待入库状态变为「已完成」
3. **员工 AI 问答**（F-02-01/02）— `/employee` 新建会话，提问与知识库相关的问题，查看 AI 回复与引用卡片
4. **转人工**（F-02-03）— 同会话点击「转人工」，状态变为排队中
5. **坐席接单**（F-03-03）— 另开标签页 `/agent`，待处理列表出现新工单，点击「接单」
6. **坐席回复**（F-03-04）— 坐席发送文字；员工端标签页应**实时**收到（WebSocket，无需刷新）
7. **智能回复**（F-03-05）— 坐席点「智能回复」，选一条候选填入输入框，**手动点发送**（不会自动发送）
8. **工单归类**（F-03-06）— 选择 IT/HR/财务/行政/其他 并保存
9. **结束工单**（F-03-07）— 点击「结束工单」；员工端会话**实时**变只读，不可再发送
10. **导航** — 顶部可在员工端、坐席端、知识库之间切换（F-02-07 / F-03-08 / F-04-06）

**双标签页验收**：同一账号同时打开 `/employee` 与 `/agent`，用于验证 WebSocket 实时推送。

---

## 自动化测试

```powershell
# 后端单元/集成测试
cd d:\zhinengkefu\SDD_V7_1_2\SDD_V7_1_2\Projects_Repo\1\backend
$env:PYTHONPATH=".."
..\.venv\Scripts\python.exe -m pytest tests -q

# 前端构建
cd d:\zhinengkefu\SDD_V7_1_2\SDD_V7_1_2\Projects_Repo\1\frontend
npm run build
```

---

## 常见问题

**Q：页面空白 / 无法访问**
- 确认**窗口 2** 的前端还在跑
- 地址用 `http://127.0.0.1:5199`，不要用 `localhost` 混用不同端口

**Q：接口 404 或连不上**
- 确认**窗口 1** 后端还在跑
- `frontend/.env` 中 `VITE_BACKEND_PROXY_TARGET=http://localhost:8099`
- 新增 API 路由后须**重启后端**

**Q：WebSocket 不推送**
- 确认后端已重启（`/ws/messages` 路由需加载）
- 浏览器 Network 中应看到 `ws://127.0.0.1:5199/ws/messages` 状态为 **101**
- `VITE_USE_MOCK` 须为 `false`

**Q：RAG / 智能回复很慢**
- 百炼 API 调用通常需 10～30 秒，属正常现象；前端已配置 120 秒超时

**Q：改代码后不生效**
- 重启对应窗口（先 Ctrl+C 停止，再重新执行脚本）

**Q：知识库入库失败**
- 检查 `DASHSCOPE_API_KEY` 是否配置
- 点击「查看错误」查看具体原因；超长段落会自动切块
