# 算法道场 (AlgoDojo)

面向 0 基础初学者系统学习算法思路、并训练面试手撕能力的在线刷题判题平台（Online Judge）。

## 项目简介

用户在网页内嵌的代码编辑器中作答，后端通过独立 Docker 容器沙箱安全执行用户提交的代码，并用预置测试用例自动判题。平台在判题能力之上叠加面向初学者的学习辅助体系：专题路线图、分层提示、套路速查。

## 技术栈

- **前端**：React + TypeScript + Monaco Editor
- **后端**：Python / FastAPI（异步判题调度）
- **判题执行**：独立 Docker 容器沙箱（强隔离、资源限制、禁网）
- **存储**：PostgreSQL + Redis
- **认证**：GitHub OAuth + JWT

## 核心特性（第一版 MVP）

- 在线判题：网页内写代码、运行、提交，安全沙箱执行
- 多语言：Python / TypeScript 二选一作答
- 题库：LeetCode 热题 Hot 100，按专题分类
- 学习辅助：专题路线图、分层提示、套路/模板速查

## 文档

- [需求文档](./requirements.md)
- [技术设计](./design.md)
- [实施任务清单](./tasks.md)
- [初始题库](./hot100.md)

## 仓库结构

```
AlgoDojo/
├── backend/    # FastAPI 后端 API（uv + ruff + pytest）
├── frontend/   # React + TypeScript + Vite 前端
├── judge/      # 判题沙箱镜像与执行引擎（待实现）
├── deploy/     # docker-compose 本地基础设施（PostgreSQL + Redis）
└── *.md        # 需求 / 设计 / 任务 / 题库文档
```

## 本地启动

需要：Python 3.10+、Node 18+、Docker、[uv](https://docs.astral.sh/uv/)。

```bash
# 1. 启动基础设施（PostgreSQL + Redis）
docker compose -f deploy/docker-compose.yml up -d

# 2. 启动后端（新终端）
cd backend
uv sync
cp .env.example .env
uv run uvicorn app.main:app --reload --port 8000
#    健康检查： http://localhost:8000/health
#    就绪检查： http://localhost:8000/health/ready  (校验 PG + Redis)

# 3. 启动前端（新终端）
cd frontend
npm install
npm run dev
#    打开 http://localhost:5173 ，首页会显示后端连接状态
```

各子项目的详细说明见 `backend/README.md`、`frontend/README.md`、`deploy/README.md`、`judge/README.md`。

## 状态

✅ 第一版（MVP）已完成（tasks.md 阶段 0-7，任务 1-21）：
- 阶段 0 脚手架与基础设施（任务 1-2）
- 阶段 1 数据模型 + hot100 题库导入（任务 3-4）
- 阶段 2 GitHub OAuth + JWT 登录（任务 5-6）
- 阶段 3 判题沙箱（镜像/运行器/执行引擎/verdict，任务 7-10）
- 阶段 4 提交受理 + 异步判题 Worker + 结果查询（任务 11-13）
- 阶段 5 题库浏览 + 进度追踪 + 前端题库/题目页（任务 14-16）
- 阶段 6 学习辅助：专题路线图 / 分层提示 / 套路速查（任务 17-19）
- 阶段 7 质量保障（鉴权/数据隔离/沙箱安全/日志脱敏测试）+ 容器化部署（任务 20-21）

核心闭环已端到端跑通：登录 → 浏览题库 → 在 Monaco 编辑器作答 → 运行/提交 → 安全沙箱判题 → 查看结果与进度；并叠加路线图、分层提示、套路速查等学习辅助。完整后端栈（API + Worker + PostgreSQL + Redis）已容器化编排，见 `deploy/README.md`。
