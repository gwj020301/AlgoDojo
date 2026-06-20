# 题库种子数据（Seed）

`problems.yaml` 是题库的种子数据源，由 `hot100.md` 解析 + 人工编辑数据（`app/seed/curated.py`）合成。

## 文件

- `problems.yaml` —— **正式种子**，`loader` 读取它写入数据库（已纳入版本管理）。
- `problems.draft.yaml` —— 纯解析草稿（无编辑数据），仅供参考，不纳入版本管理。

## 数据格式

```yaml
topics:
  - name: 哈希
    order_index: 0                      # 难度梯度排序
    pattern_summary: "..."              # 专题套路总结
    recommended_problem_numbers: [1, 2, 3]   # 路线图推荐题序（题号）
problems:
  - number: 1                           # hot100 题号（唯一）
    title: 两数之和
    topic: 哈希
    difficulty: easy                    # easy | medium | hard
    languages: [python, typescript]
    description: "给定一个整数数组 ..."
    reference_solution: "..."           # 可为 null
    templates:                          # 各语言初始代码模板
      python: "class Solution: ..."
      typescript: "function twoSum(...) {...}"
    test_cases:                         # 判题用例
      - input: '{"nums": [2,7,11,15], "target": 9}'   # JSON 入参
        expected_output: "[0, 1]"                       # JSON 返回值
        is_sample: true                                 # 样例（用于"运行/自测"）
    hints:                              # 分层提示 level 1..4
      - { level: 1, content: "..." }
```

> 测试用例 I/O 约定：`input` 为函数入参的 JSON 对象，`expected_output` 为返回值的 JSON。
> 该约定将随判题运行器（tasks.md 阶段 3，任务 8/10）最终确定。

## 命令

```bash
# 重新生成正式种子（解析 hot100.md + 合并 curated 编辑数据）
uv run python -m app.seed.generate

# 生成纯解析草稿
uv run python -m app.seed.generate --draft

# 导入数据库（幂等：按 topic 名 / 题号 upsert，可重复执行）
uv run python -m app.seed.loader
```

## 状态

- 全部 100 题的 题号 / 标题 / 专题 / 题干 已由解析自动生成。
- 难度、测试用例、参考题解、代码模板、分层提示需逐题人工补充
  （目前已完整示例：#1 两数之和、#81 爬楼梯）。补充方式：编辑 `app/seed/curated.py` 后重新生成。
