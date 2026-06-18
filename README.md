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

## 状态

🚧 规划阶段（Spec 已完成，待开始实现）
