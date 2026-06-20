# AlgoDojo Backend (FastAPI)

异步判题调度后端，提供认证、题库、提交受理、判题结果查询等 API。

## 技术栈

- Python 3.10+ / FastAPI
- SQLAlchemy 2.0 (async) + asyncpg → PostgreSQL
- redis-py (async) → Redis
- 依赖管理：uv；lint/format：ruff

## 本地开发

```bash
# 1. 安装依赖（在 backend/ 目录下）
uv sync

# 2. 准备环境变量
cp .env.example .env

# 3. 启动依赖服务（PostgreSQL + Redis）
#    在仓库根目录执行：
#    docker compose -f deploy/docker-compose.yml up -d

# 4. 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000
```

打开 http://localhost:8000/docs 查看 API 文档。

- `GET /health` — 存活探针
- `GET /health/ready` — 就绪探针（校验 PostgreSQL + Redis 连通性）

## 质量

```bash
uv run ruff check .      # lint
uv run ruff format .     # format
uv run pytest            # 测试
```

## 数据库迁移（Alembic）

```bash
# 应用迁移（需先启动 PostgreSQL）
uv run alembic upgrade head

# 修改模型后生成新迁移
uv run alembic revision --autogenerate -m "描述"

# 校验模型与迁移是否一致
uv run alembic check
```

## 题库种子

```bash
uv run python -m app.seed.generate    # 由 hot100.md 生成 seed/problems.yaml
uv run python -m app.seed.loader      # 幂等导入数据库
```

详见 `seed/README.md`。

## 提交判题（异步）

```bash
# 启动判题 Worker（消费 Redis 队列，调用判题沙箱镜像）
# 需先构建沙箱镜像：docker build -t algodojo-judge:latest ../judge
uv run python -m app.submissions.worker
```

- `POST /submissions`（鉴权）：校验题目/语言，建 submission(queued)，入队 Redis，返回 id
- `GET /submissions/{id}`（鉴权，仅本人）：返回 status / verdict / 失败用例 / 错误详情

Worker 从 Redis 队列取任务 → 调用 `dojo_judge` 沙箱引擎 → 回写 verdict。并发上限由
`JUDGE_CONCURRENCY` 控制，超出的提交在队列中排队；沙箱/系统错误标记 `system_error`
并重试（`JUDGE_MAX_ATTEMPTS`）。

## 目录结构

```
backend/
├── app/
│   ├── main.py          # FastAPI app + 健康检查
│   ├── config.py        # pydantic-settings 配置
│   ├── db.py            # SQLAlchemy async engine/session + JSONType
│   ├── constants.py     # 领域常量（语言/难度/状态/verdict 等）
│   ├── redis_client.py  # Redis 客户端
│   ├── models/          # ORM 模型（User/Topic/Problem/TestCase/Hint/
│   │                    #   Submission/UserProblemStatus/RoadmapNode/PatternTemplate）
│   ├── auth/            # GitHub OAuth + JWT 鉴权
│   ├── submissions/     # 提交受理 + Redis 队列 + 判题 Worker
│   └── seed/            # hot100 解析 + 种子生成/导入
├── alembic/             # 数据库迁移
├── seed/                # 种子数据（problems.yaml）
├── tests/
└── pyproject.toml
```
