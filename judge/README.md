# AlgoDojo Judge（判题层）

判题沙箱镜像与执行引擎。**系统安全与技术含量的核心**：用户提交的代码一律不可信，
只在强隔离、资源受限、无网络的一次性容器中执行。

执行模型：**整程序 stdin → stdout**。用户代码是完整程序，运行器对每个测试用例
把 `input` 喂给标准输入、捕获标准输出，与期望输出按行（容忍尾随空白）比对。

## 结构

```
judge/
├── Dockerfile            # 沙箱镜像：Python3 + Node + tsc + @types/node，非 root
├── dojo_judge/
│   ├── types.py          # Verdict / TestCaseSpec / Limits / JudgeResult / JobSpec
│   ├── compare.py        # 输出规范化与比对（容忍尾随空白/换行）
│   ├── adapters.py       # 语言适配：python 直接执行；TS 经 tsc 编译后 node 执行
│   ├── runner.py         # 容器内入口（stdlib only）：编译检查 + 逐用例执行 + verdict
│   └── engine.py         # 宿主侧 Docker 执行引擎（加固 + TLE/MLE + 销毁清理）
└── tests/                # 单测（无 docker）+ 集成测试（真实容器，标记 integration）
```

## 沙箱加固（requirement 4.1-4.4）

引擎对每次提交启动一个一次性容器，参数：

- `--network none` 完全禁网
- `--user 65534:65534` 非 root（nobody）
- `--read-only` 根只读 + `--tmpfs /tmp`（仅 /tmp 可写），用户代码 `/work` 只读挂载
- `--cpus` / `--memory` + `--memory-swap`（禁用 swap）/ `--pids-limit`（防 fork 炸弹）
- `--cap-drop ALL` + `--security-opt no-new-privileges`

verdict 判定：

| verdict | 触发 |
| --- | --- |
| AC | 全部用例输出匹配 |
| WA | 某用例不匹配，返回首个失败用例 input/expected/actual |
| TLE | 用例超过墙钟时限（容器内 per-case 超时；引擎墙钟超时为兜底强杀）|
| MLE | 容器被 OOM 杀死（引擎检测 `State.OOMKilled` / 退出码 137）|
| CE | 编译/语法检查失败（Python ast 语法检查、TS tsc 类型检查）|
| RE | 用户程序非零退出 / 抛异常 |
| SE | 沙箱/基础设施错误（非用户责任）|

## 使用

```bash
# 构建镜像
docker build -t algodojo-judge:latest judge/

# 安装依赖并测试（在 judge/ 目录）
uv sync
uv run pytest -m "not integration"   # 单测，无需 docker
uv run pytest -m integration         # 集成测试，需 docker + 已构建镜像
uv run pytest                        # 全部
```

程序化调用：

```python
from dojo_judge import judge, Language, TestCaseSpec, Limits

result = judge(
    Language.PYTHON,
    code="import sys\na,b=map(int,sys.stdin.read().split())\nprint(a+b)\n",
    cases=[TestCaseSpec("2 3", "5"), TestCaseSpec("10 20", "30")],
    limits=Limits(time_limit_s=2.0, memory_limit_mb=256),
)
print(result.verdict)  # AC / WA / TLE / MLE / CE / RE / SE
```

## 安全提示（部署）

> Worker 拉起判题容器需访问 Docker daemon。挂载 docker.sock 有提权风险，
> 生产环境建议使用专用判题节点或远程 Docker API 隔离（见 design.md 第九节）。
> 容器加固为最低要求，后续可引入 gVisor/Firecracker 进一步增强隔离。

## 状态

✅ 已实现并验证（tasks.md 阶段 3，任务 7-10）：镜像、多语言运行器、执行引擎、verdict 判定。
集成测试覆盖 AC/WA/TLE/MLE/CE/RE 各场景，以及禁网、非 root 验证。
