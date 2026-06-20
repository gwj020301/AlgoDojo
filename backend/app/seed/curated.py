"""Curated overlay data for the seed.

The hot100 parser gives us topic / number / title / description for all 100
problems. Everything else (difficulty, reference solution, code templates, test
cases, layered hints, topic pattern summaries) is editorial and lives here.

- ``TOPIC_SUMMARIES``: short 套路总结 per topic (requirement 6.2).
- ``CURATED_PROBLEMS``: per-problem full data, keyed by problem number. A couple
  of problems are fully populated as worked examples; the rest can be filled in
  incrementally.

Test-case I/O convention (until the judge runner finalizes it, design tasks 8/10):
``input`` is a JSON object of the function arguments and ``expected_output`` is
the JSON-encoded return value.
"""

from __future__ import annotations

from typing import Any

from app.constants import Difficulty, Language

TOPIC_SUMMARIES: dict[str, str] = {
    "哈希": "用哈希表以空间换时间，把“查找是否存在/出现次数”从 O(n) 降到 O(1)。",
    "双指针": "在有序或可单调推进的数组上，用两个指针相向或同向移动，避免嵌套循环。",
    "滑动窗口": "维护一个可伸缩的窗口与窗口内统计量，左右指针只进不退，整体 O(n)。",
    "子串": "前缀和 / 哈希 / 单调队列等技巧处理连续子数组（子串）的统计问题。",
    "普通数组": "数组上的经典技巧：前缀积、原地标记、贪心扫描、区间合并。",
    "矩阵": "二维数组的遍历与原地变换：方向数组、边界收缩、转置+翻转。",
    "链表": "虚拟头节点、快慢指针、翻转与拼接是链表题的三板斧。",
    "二叉树": "递归是二叉树的天然解法：明确返回值、单层逻辑与终止条件。",
    "图论": "建图后用 BFS/DFS 遍历；拓扑排序处理依赖；并查集处理连通性。",
    "回溯": "决策树上的 DFS：选择 → 递归 → 撤销选择，注意剪枝与去重。",
    "二分查找": "在单调性上折半收缩区间，关键是写对边界与循环不变量。",
    "栈": "用栈处理“后进先出”“最近匹配”“单调性”类问题。",
    "堆": "用优先队列动态维护 Top-K / 中位数 / 合并多路有序数据。",
    "贪心算法": "每一步取局部最优，并证明可推出全局最优。",
    "动态规划": "定义状态、写出转移方程、确定边界与计算顺序。",
    "多维动态规划": "状态扩展到二维（网格 / 双串），按依赖顺序填表。",
    "技巧": "位运算、摩尔投票、三向切分等巧解，常要求常数空间。",
}


def _two_sum() -> dict[str, Any]:
    return {
        "difficulty": Difficulty.EASY,
        "reference_solution": (
            "用哈希表存放 值->下标。遍历时查 target-num 是否已出现，"
            "命中即返回两个下标，时间 O(n)、空间 O(n)。"
        ),
        "templates": {
            Language.PYTHON: (
                "class Solution:\n"
                "    def twoSum(self, nums: list[int], target: int) -> list[int]:\n"
                "        # TODO: 实现\n"
                "        pass\n"
            ),
            Language.TYPESCRIPT: (
                "function twoSum(nums: number[], target: number): number[] {\n"
                "  // TODO: 实现\n"
                "  return [];\n"
                "}\n"
            ),
        },
        "test_cases": [
            {
                "input": '{"nums": [2, 7, 11, 15], "target": 9}',
                "expected_output": "[0, 1]",
                "is_sample": True,
            },
            {
                "input": '{"nums": [3, 2, 4], "target": 6}',
                "expected_output": "[1, 2]",
                "is_sample": False,
            },
            {
                "input": '{"nums": [3, 3], "target": 6}',
                "expected_output": "[0, 1]",
                "is_sample": False,
            },
        ],
        "hints": [
            {"level": 1, "content": "暴力是 O(n^2) 双重循环，想想如何用额外空间换时间。"},
            {"level": 2, "content": "遍历时，对每个 num 需要快速判断 target-num 是否出现过。"},
            {
                "level": 3,
                "content": "seen = {}; for i, x in nums: if target-x in seen: "
                "return [seen[target-x], i]; seen[x] = i",
            },
            {"level": 4, "content": "用哈希表记录 值->下标，一次遍历即可，时间/空间均 O(n)。"},
        ],
    }


def _climb_stairs() -> dict[str, Any]:
    return {
        "difficulty": Difficulty.EASY,
        "reference_solution": (
            "f(n)=f(n-1)+f(n-2)，即斐波那契。用两个变量滚动递推，时间 O(n)、空间 O(1)。"
        ),
        "templates": {
            Language.PYTHON: (
                "class Solution:\n"
                "    def climbStairs(self, n: int) -> int:\n"
                "        # TODO: 实现\n"
                "        pass\n"
            ),
            Language.TYPESCRIPT: (
                "function climbStairs(n: number): number {\n  // TODO: 实现\n  return 0;\n}\n"
            ),
        },
        "test_cases": [
            {"input": '{"n": 2}', "expected_output": "2", "is_sample": True},
            {"input": '{"n": 3}', "expected_output": "3", "is_sample": False},
            {"input": '{"n": 5}', "expected_output": "8", "is_sample": False},
        ],
        "hints": [
            {"level": 1, "content": "到达第 n 阶，最后一步只能从 n-1 或 n-2 上来。"},
            {"level": 2, "content": "因此方法数 f(n) = f(n-1) + f(n-2)。"},
            {"level": 3, "content": "a, b = 1, 1; 重复 n-1 次: a, b = b, a+b; 返回 b。"},
            {"level": 4, "content": "本质是斐波那契数列，滚动变量即可 O(1) 空间。"},
        ],
    }


# Per-problem curated data, keyed by problem number.
CURATED_PROBLEMS: dict[int, dict[str, Any]] = {
    1: _two_sum(),
    81: _climb_stairs(),
}


# Reusable algorithm pattern templates for the cheat-sheet (requirement 8).
# Each entry: pattern_name + per-language code + mnemonic (口诀).
PATTERN_TEMPLATES: list[dict[str, Any]] = [
    {
        "pattern_name": "滑动窗口",
        "mnemonic": "右扩入窗，越界则左缩；窗口合法时更新答案。",
        "code": {
            Language.PYTHON: (
                "def sliding_window(s: str) -> int:\n"
                "    left = 0\n"
                "    window = {}\n"
                "    best = 0\n"
                "    for right, c in enumerate(s):\n"
                "        window[c] = window.get(c, 0) + 1\n"
                "        while window[c] > 1:  # 收缩条件\n"
                "            window[s[left]] -= 1\n"
                "            left += 1\n"
                "        best = max(best, right - left + 1)\n"
                "    return best\n"
            ),
            Language.TYPESCRIPT: (
                "function slidingWindow(s: string): number {\n"
                "  let left = 0, best = 0;\n"
                "  const window = new Map<string, number>();\n"
                "  for (let right = 0; right < s.length; right++) {\n"
                "    const c = s[right];\n"
                "    window.set(c, (window.get(c) ?? 0) + 1);\n"
                "    while ((window.get(c) ?? 0) > 1) {\n"
                "      window.set(s[left], window.get(s[left])! - 1);\n"
                "      left++;\n"
                "    }\n"
                "    best = Math.max(best, right - left + 1);\n"
                "  }\n"
                "  return best;\n"
                "}\n"
            ),
        },
    },
    {
        "pattern_name": "二分查找",
        "mnemonic": "循环不变量：答案落在 [lo, hi]；mid 偏左，按条件收缩半区。",
        "code": {
            Language.PYTHON: (
                "def binary_search(nums: list[int], target: int) -> int:\n"
                "    lo, hi = 0, len(nums) - 1\n"
                "    while lo <= hi:\n"
                "        mid = (lo + hi) // 2\n"
                "        if nums[mid] == target:\n"
                "            return mid\n"
                "        if nums[mid] < target:\n"
                "            lo = mid + 1\n"
                "        else:\n"
                "            hi = mid - 1\n"
                "    return -1\n"
            ),
            Language.TYPESCRIPT: (
                "function binarySearch(nums: number[], target: number): number {\n"
                "  let lo = 0, hi = nums.length - 1;\n"
                "  while (lo <= hi) {\n"
                "    const mid = (lo + hi) >> 1;\n"
                "    if (nums[mid] === target) return mid;\n"
                "    if (nums[mid] < target) lo = mid + 1;\n"
                "    else hi = mid - 1;\n"
                "  }\n"
                "  return -1;\n"
                "}\n"
            ),
        },
    },
    {
        "pattern_name": "回溯",
        "mnemonic": "选择 → 递归 → 撤销选择；进入前剪枝，路径满足即收集。",
        "code": {
            Language.PYTHON: (
                "def backtrack(nums: list[int]) -> list[list[int]]:\n"
                "    res, path = [], []\n"
                "    def dfs(start: int) -> None:\n"
                "        res.append(path[:])\n"
                "        for i in range(start, len(nums)):\n"
                "            path.append(nums[i])\n"
                "            dfs(i + 1)\n"
                "            path.pop()  # 撤销选择\n"
                "    dfs(0)\n"
                "    return res\n"
            ),
            Language.TYPESCRIPT: (
                "function backtrack(nums: number[]): number[][] {\n"
                "  const res: number[][] = [], path: number[] = [];\n"
                "  const dfs = (start: number): void => {\n"
                "    res.push([...path]);\n"
                "    for (let i = start; i < nums.length; i++) {\n"
                "      path.push(nums[i]);\n"
                "      dfs(i + 1);\n"
                "      path.pop();\n"
                "    }\n"
                "  };\n"
                "  dfs(0);\n"
                "  return res;\n"
                "}\n"
            ),
        },
    },
    {
        "pattern_name": "广度优先搜索",
        "mnemonic": "队列逐层扩展，入队即标记已访问，适合最短路/层序。",
        "code": {
            Language.PYTHON: (
                "from collections import deque\n\n"
                "def bfs(start, neighbors) -> int:\n"
                "    q = deque([start])\n"
                "    seen = {start}\n"
                "    steps = 0\n"
                "    while q:\n"
                "        for _ in range(len(q)):\n"
                "            node = q.popleft()\n"
                "            for nxt in neighbors(node):\n"
                "                if nxt not in seen:\n"
                "                    seen.add(nxt)\n"
                "                    q.append(nxt)\n"
                "        steps += 1\n"
                "    return steps\n"
            ),
            Language.TYPESCRIPT: (
                "function bfs(start: number, neighbors: (n: number) => number[]): number {\n"
                "  const q: number[] = [start];\n"
                "  const seen = new Set<number>([start]);\n"
                "  let steps = 0;\n"
                "  while (q.length) {\n"
                "    const size = q.length;\n"
                "    for (let i = 0; i < size; i++) {\n"
                "      const node = q.shift()!;\n"
                "      for (const nxt of neighbors(node)) {\n"
                "        if (!seen.has(nxt)) { seen.add(nxt); q.push(nxt); }\n"
                "      }\n"
                "    }\n"
                "    steps++;\n"
                "  }\n"
                "  return steps;\n"
                "}\n"
            ),
        },
    },
]
