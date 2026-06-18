# 实施任务清单 — 算法道场 (AlgoDojo)

> 任务按依赖顺序编排，建议从上到下推进。每个任务标注了对应的需求编号（见 requirements.md）。
> 约定：后端 Python/FastAPI，前端 React/TS，存储 PostgreSQL + Redis，判题用 Docker 沙箱。

## 阶段 0：项目脚手架与基础设施

- [ ] 1. 初始化仓库结构与开发环境
  - 创建 monorepo 目录结构：`backend/`、`frontend/`、`judge/`、`deploy/`
  - 后端初始化 FastAPI 项目（依赖管理用 uv/poetry），配置 lint/format（ruff + black）
  - 前端初始化 React + TypeScript + Vite 项目，配置 ESLint/Prettier
  - 编写根 `README.md` 与本地启动说明
  - _需求：技术栈基线_

- [ ] 2. 搭建本地基础设施（docker-compose）
  - 编写 `deploy/docker-compose.yml`：PostgreSQL、Redis 服务
  - 后端接入数据库连接（SQLAlchemy + asyncpg）与 Redis 客户端
  - 配置环境变量管理（pydantic-settings，区分 dev/prod）
  - 验证后端能连通 PG 与 Redis
  - _需求：可部署性 1_

## 阶段 1：数据模型与题库导入

- [ ] 3. 定义数据库模型与迁移
  - 用 SQLAlchemy 定义模型：User、Topic、Problem、TestCase、Hint、Submission、UserProblemStatus、RoadmapNode、PatternTemplate
  - 引入 Alembic 配置并生成初始迁移
  - _需求：1.2/1.3、2.2、5、6、7、8_

- [ ] 4. 实现题库导入脚本（hot100）
  - 编写解析 `hot100.md` 的脚本，按专题分组提取题号/标题/题干/分类
  - 设计种子数据格式（JSON/YAML），补充难度、测试用例、参考题解、各语言模板
  - 编写 seed 命令将题库、专题、路线图节点写入数据库
  - 单元测试：解析与导入正确性
  - _需求：2.1、2.2、6.1、6.4_

## 阶段 2：用户认证（GitHub OAuth + JWT）

- [ ] 5. 实现 GitHub OAuth 登录后端
  - `GET /auth/github/login` 重定向到 GitHub 授权页
  - `GET /auth/github/callback` 处理回调、换取 token、拉取用户信息、创建/更新 User、首登初始化进度
  - 签发 JWT；实现 JWT 鉴权依赖（FastAPI Depends）
  - 失败/拒绝场景返回明确错误；不申请仓库写权限
  - 单元测试：回调成功/失败、JWT 校验、401 场景
  - _需求：1.1-1.7_

- [ ] 6. 前端登录流与鉴权
  - 登录页 + "使用 GitHub 登录"按钮
  - 处理回调、存储 JWT、请求拦截器附带 token、401 跳登录
  - 失败提示与停留登录页
  - _需求：1.1、1.5、1.6_

## 阶段 3：判题沙箱（核心，可独立开发）

- [ ] 7. 构建判题沙箱镜像
  - 编写 `judge/Dockerfile`：基础镜像 + Python3 + Node + TypeScript 运行时
  - 内置非 root 运行用户
  - 验证镜像可运行简单 Python 与 TS 程序
  - _需求：4.4、可部署性 2_

- [ ] 8. 实现多语言运行器（runner）适配
  - 定义统一接口 `prepare(code) -> 执行命令`
  - Python 适配器：直接执行
  - TypeScript 适配器：编译（区分 CE）后执行
  - 单元测试：编译失败/运行成功路径
  - _需求：3.2、4.7_

- [ ] 9. 实现沙箱执行引擎（容器加固）
  - 封装 Docker 启动参数：`--rm`、`--network none`、`--user`、`--read-only`、`--tmpfs /tmp`、`--cpus`、`--memory`、`--memory-swap`、`--pids-limit`、`--cap-drop ALL`、seccomp
  - 实现墙钟超时强杀（→ TLE）、内存超限识别（→ MLE）
  - 容器执行完销毁并清理临时目录
  - 测试：死循环→TLE、大内存→MLE、禁网验证、非 root 验证
  - _需求：4.1-4.4、4.9_

- [ ] 10. 实现判题判定逻辑（verdict）
  - 逐用例运行、输出比对，得出 AC/WA/TLE/MLE/CE/RE
  - WA 时返回首个失败用例的输入/期望/实际
  - 记录运行耗时
  - 单元测试：覆盖全部 verdict 分支
  - _需求：4.5-4.7_

## 阶段 4：提交受理与异步判题调度

- [ ] 11. 实现提交受理 API 与任务入队
  - `POST /submissions`：校验题目/语言、创建 submission(status=queued)、入队 Redis
  - 返回 submission_id
  - _需求：4.8、5.1_

- [ ] 12. 实现判题 Worker 与队列消费
  - Worker 从 Redis 取任务 → 更新 running → 调用沙箱引擎 → 写回 verdict/done
  - 并发上限控制与任务排队（不拒绝/不崩溃）
  - 异常处理：沙箱/Worker 失败标记 system_error 并可重试，日志脱敏
  - 集成测试：提交→入队→判题→结果回写全链路
  - _需求：4.8、4.10、错误处理_

- [ ] 13. 实现判题结果查询 API
  - `GET /submissions/{id}`：返回 status + verdict + 失败用例详情
  - 用户数据隔离（仅本人可查）
  - _需求：4.8、安全 2_

## 阶段 5：题库浏览与作答

- [ ] 14. 实现题库与题目 API
  - `GET /problems`：列表 + 完成状态 + 按专题/难度/状态筛选
  - `GET /problems/{id}`：题干 + 可选语言 + 模板
  - `GET /problems/{id}/submissions`：历史提交
  - _需求：2.3-2.6、5.5_

- [ ] 15. 实现进度追踪
  - 提交完成后更新 UserProblemStatus（首次 AC→已通过，未过→进行中）
  - `GET /me/progress`：总体进度 + 按专题完成率
  - 单元测试：状态机流转
  - _需求：5.1-5.4_

- [ ] 16. 实现题库列表与题目页前端
  - 题库列表页：按专题分组、筛选、完成状态标识
  - 题目页布局：左题干 / 右 Monaco 编辑器 / 结果面板
  - 语言切换加载模板（切换前提示）、localStorage 草稿暂存
  - "运行/提交"操作 + 轮询结果展示（排队中/执行中/完成）
  - _需求：2.3、2.4、3.1-3.5、4.8_

## 阶段 6：学习辅助功能

- [ ] 17. 实现专题路线图
  - `GET /roadmap`：返回难度梯度专题序列 + 套路总结 + 进度 + 推荐题序
  - 前端路线图页：展示路径、专题进度、推荐题入口
  - _需求：6.1-6.4_

- [ ] 18. 实现分层提示系统
  - `GET /problems/{id}/hints?level=n`：逐级返回，默认不直接给完整题解
  - 记录提示使用情况
  - 前端：提示抽屉，逐级解锁，解锁完整题解前二次确认
  - _需求：7.1-7.4_

- [ ] 19. 实现套路/模板速查
  - `GET /patterns`：套路列表 + Python/TS 模板 + 口诀，支持关键词检索
  - 题目页提供跳转到相关专题套路的入口
  - 前端套路速查页
  - _需求：8.1-8.4_

## 阶段 7：质量保障与部署

- [ ] 20. 完善测试与安全校验
  - 补齐 API 鉴权与用户数据隔离测试（A 不能读 B 的数据）
  - 沙箱安全用例回归（禁网、非 root、资源限制）
  - 日志脱敏校验（不含 JWT/OAuth token）
  - _需求：安全 1-3、测试策略_

- [ ] 21. 容器化与部署编排
  - 为 API、Worker 编写 Dockerfile
  - 完善 `docker-compose.yml`（API/Worker/PG/Redis/判题镜像）
  - 文档化 Docker daemon 访问方案与提权风险缓解（专用判题节点/远程 Docker API）
  - 编写部署与运行文档
  - _需求：可部署性 1-2、部署章节_
