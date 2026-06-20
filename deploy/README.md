# AlgoDojo Deploy（部署与本地基础设施）

`deploy/docker-compose.yml` 编排完整后端栈：**PostgreSQL + Redis + API + Worker**，
外加一个一次性 `init` 服务（执行数据库迁移 + 题库种子导入）。

## 一、仅基础设施（本地开发用）

只起 PostgreSQL + Redis，后端/前端在本机用 uv/npm 跑：

```bash
docker compose -f deploy/docker-compose.yml up -d postgres redis
```

| 服务 | 端口 | 默认凭据 |
| --- | --- | --- |
| PostgreSQL 16 | 5432 | algodojo / algodojo，库名 algodojo |
| Redis 7 | 6379 | 无密码（本地开发） |

## 二、完整栈（容器化）

### 前置

```bash
# 1) 构建判题沙箱镜像（Worker 通过宿主 Docker 守护进程拉起它）
docker build -t algodojo-judge:latest judge/

# 2) 准备环境变量
cp deploy/.env.example deploy/.env   # 填入 GitHub OAuth、JWT_SECRET
```

### 启动

```bash
docker compose -f deploy/docker-compose.yml up -d --build
```

启动顺序：`postgres`/`redis`（健康检查）→ `init`（`alembic upgrade head` + 种子导入，运行后退出）→ `api`（:8000）/ `worker`。

- API 文档： http://localhost:8000/docs
- 就绪检查： http://localhost:8000/health/ready

镜像为多阶段构建（`deploy/Dockerfile`）：`api` 目标跑 uvicorn；`worker` 目标在同一基础上加入 `docker` CLI，用于在宿主守护进程上拉起判题容器。

## 三、⚠️ Docker daemon 访问与提权风险

判题 Worker 需要拉起判题容器，因此 compose 把宿主的 `/var/run/docker.sock` 挂载进 Worker 容器：

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock
```

**风险**：挂载 docker.sock 等价于把宿主 root 权限交给 Worker 容器——一旦 Worker 进程被攻破（它本就在执行不可信的用户代码调度），攻击者可控制整个宿主 Docker，进而逃逸到宿主机。

**缓解方案（按推荐度）**：

1. **专用判题节点**：把 Worker + 判题容器隔离到一台独立、最小权限、可随时重建的机器/VM，与 API、数据库网络隔离；即使被攻破，爆炸半径受限。
2. **远程 Docker API（mTLS）**：Worker 通过 TLS 双向认证连接专用判题主机的 Docker API（`DOCKER_HOST`），而非挂载本地 socket，避免与业务同宿主。
3. **更强隔离运行时**：判题容器改用 gVisor（`runsc`）或 Kata/Firecracker microVM，进一步隔离内核（design.md 已提及）。
4. **rootless / 受限 socket 代理**：用 rootless Docker，或在 socket 前加代理（如 docker-socket-proxy）只放行 `containers create/start/wait/rm`、禁用危险 API。

第一版（MVP）采用挂载 socket 的最简方案以打通闭环；**生产部署务必采用上述至少一种缓解措施**。判题容器本身已做强加固（`--network none`、非 root、只读根、`--cap-drop ALL`、CPU/内存/PID 限制，见 `judge/README.md`）。

## 四、常用命令

```bash
docker compose -f deploy/docker-compose.yml ps             # 状态
docker compose -f deploy/docker-compose.yml logs -f worker # Worker 日志
docker compose -f deploy/docker-compose.yml down           # 停止
docker compose -f deploy/docker-compose.yml down -v        # 停止并清除数据卷
```

## 五、镜像单独构建

```bash
docker build -f deploy/Dockerfile --target api    -t algodojo-api .      # 构建上下文为仓库根
docker build -f deploy/Dockerfile --target worker -t algodojo-worker .
```
