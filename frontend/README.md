# AlgoDojo Frontend (React + TypeScript + Vite)

题库浏览、内嵌 Monaco 代码编辑器、判题结果展示、学习辅助（路线图/分层提示/套路速查）等 Web 界面。

## 技术栈

- React 18 + TypeScript
- Vite 5（开发服务器 + 构建）
- ESLint + Prettier

## 本地开发

```bash
npm install
npm run dev      # 启动开发服务器 http://localhost:5173
```

开发服务器会把 `/api/*` 代理到后端 `http://localhost:8000`（见 vite.config.ts），
因此需要先启动后端服务。

## 脚本

```bash
npm run build         # 类型检查 + 生产构建
npm run lint          # ESLint
npm run format        # Prettier 格式化
npm run preview       # 预览生产构建
```

## 说明

- 当前为脚手架 + 登录鉴权。路由：`/login`（GitHub 登录页）、`/auth/callback`（OAuth 回调，
  从 URL fragment 取 JWT 存入 localStorage）、`/`（受保护首页，显示当前用户）。
- 鉴权：`src/api/client.ts` 作为请求拦截器，为每个请求附带 `Authorization: Bearer <jwt>`，
  收到 401 时清除 token 并跳转 `/login`（会话过期）。
- 「使用 GitHub 登录」按钮整页跳转到后端 `${VITE_BACKEND_URL}/auth/github/login`，
  以确保 OAuth state cookie 设置在后端源上。其余 fetch 调用走 `/api` 代理（同源，无 CORS）。
- 配置：`VITE_BACKEND_URL`（默认 `http://localhost:8000`）。
- Monaco 编辑器、题库页、路线图等在后续任务（tasks.md 阶段 5/6）中实现。
- 已知 advisory：Vite 5 依赖的 esbuild 存在 dev-server 公告（GHSA-67mh-4wv8-2f99），
  仅影响本地开发服务器，生产构建不受影响。升级到 Vite 8 为破坏性变更，后续统一处理。
