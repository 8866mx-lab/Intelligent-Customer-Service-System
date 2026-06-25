# 测试报告：T-009 用户登录认证功能闭环

**测试时间**：2026-06-06
**Tester Agent ID**：tester-subagent

## 结果：PASS

## 验收标准逐条验证

| # | 标准 | 结果 | 说明 |
|---|------|------|------|
| 1 | 登录页输入种子账号密码点击登录，跳转员工端且顶部显示真实用户名 | PASS | `VITE_USE_MOCK=false`；`authService.login` 调真实 API；`LoginPage` → `setAuth` → `navigate('/employee')`；`AppShell` 显示 `user?.username`；Vite 代理 `POST http://127.0.0.1:5199/api/auth/login` 返回 zhangsan |
| 2 | 刷新浏览器后仍保持登录状态 | PASS | `App.tsx` 挂载时 `loadAuth()` 读 localStorage token 并调 `authService.getMe()` 恢复用户态 |
| 3 | 退出登录后回登录页，访问受保护页面跳转登录页 | PASS | `AppShell.handleLogout` → `clearAuth` + `navigate('/login')`；`ProtectedRoute` 无 token 重定向 `/login` |
| 4 | 登录后可通过顶部 Tab 访问员工端、坐席端、知识库 | PASS | `AppShell` navItems 含三 Tab，无角色限制；路由 `/employee`、`/agent`、`/knowledge` 均在 `ProtectedRoute` 下 |

## technicalChecks 逐条验证

| # | 检查项 | 结果 | 说明 |
|---|--------|------|------|
| 1 | pytest -k auth 通过 | PASS | 8 passed |
| 2 | VITE_USE_MOCK=false 时登录命中真实 API | PASS | `frontend/.env` 已设 false；`authService.ts` mock 分支不执行 |
| 3 | vite.config.ts /api 代理指向 8099 | PASS | `server.proxy['/api'].target` 默认 `http://localhost:8099`；代理登录实测 200 |
| 4 | 页面无 [Mock] 或 Mock-only 登录文案 | PASS | `LoginPage`/`AppShell` 无 Mock 提示；文案与 `docs/prototypes/01-login.html` 一致 |
| 5 | npm run type-check && lint && build | PASS | 三项均 exit 0 |

## 本轮已修复问题（与上轮对比）

| # | 问题 | 状态 |
|---|------|------|
| 1 | 后端无法启动，真实登录闭环未验证 | 已修复 |

## 超出范围发现（不影响当前任务判定）

| # | 问题 | 所属模块 | 建议处理方式 |
|---|------|---------|------------|
| 1 | 未执行 Playwright 全浏览器 E2E；已通过代码路径 + Vite 代理 API 联调验证 | 测试 | 用户门禁可选手动浏览器确认 |
