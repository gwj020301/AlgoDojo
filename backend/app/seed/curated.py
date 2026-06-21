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
        "knowledge_tips": [
            {
                "title": "什么是哈希表（Hash Table）",
                "content": (
                    "哈希表通过「哈希函数」把键（key）映射到存储位置，从而实现平均 O(1) 的"
                    "插入、删除和查找。它用空间换时间：把「某个值是否出现过 / 出现在哪」这类"
                    "查询，从遍历的 O(n) 降到接近 O(1)。\n"
                    "Python 的 dict（字典）和 set（集合）底层都是哈希表。"
                ),
            },
            {
                "title": "Python 中怎么创建和使用",
                "content": (
                    "创建：\n"
                    "· 空字典 d = {} 或 d = dict()\n"
                    "· 空集合 s = set()（注意 {} 是空字典，不是空集合）\n"
                    "常用操作（均摊 O(1)）：\n"
                    "· 增 / 改：d[key] = value\n"
                    "· 查存在：key in d\n"
                    "· 取值（带默认，避免 KeyError）：d.get(key, default)\n"
                    "· 删除：del d[key] 或 d.pop(key, None)\n"
                    "· 遍历键值：for k, v in d.items()"
                ),
                "code": {
                    Language.PYTHON: (
                        "d = {}              # 创建空字典\n"
                        "d['a'] = 1          # 写入\n"
                        "if 'a' in d:        # O(1) 判断键是否存在\n"
                        "    print(d['a'])\n"
                        "print(d.get('b', 0))  # 不存在返回默认值 0\n\n"
                        "from collections import defaultdict, Counter\n"
                        "cnt = Counter('aabbbc')   # {'a':2,'b':3,'c':1} 计数神器\n"
                        "g = defaultdict(list)     # 值默认空列表，省去判断\n"
                        "g['x'].append(1)\n"
                    ),
                    Language.TYPESCRIPT: (
                        "const m = new Map<string, number>(); // 推荐用 Map\n"
                        "m.set('a', 1);\n"
                        "if (m.has('a')) console.log(m.get('a'));\n"
                        "console.log(m.get('b') ?? 0);  // 不存在给默认值\n\n"
                        "const s = new Set<number>();   // 集合：只判存在\n"
                        "s.add(7);\n"
                        "console.log(s.has(7));\n"
                    ),
                },
            },
            {
                "title": "必备知识 / 易错点",
                "content": (
                    "1. 键必须「可哈希」：数字、字符串、元组可作键；列表、字典不可（会报 "
                    "unhashable type）。\n"
                    "2. 哈希查找是「平均」O(1)，极端情况可能退化，但刷题中按 O(1) 估算即可。\n"
                    "3. dict 从 Python 3.7 起保持「插入顺序」。\n"
                    "4. 想统计出现次数用 collections.Counter；想要默认值用 defaultdict，"
                    "比手动 if 判断更简洁。\n"
                    "5. 集合 set 适合「去重」和「只关心存在与否」的场景。"
                ),
            },
            {
                "title": "本题如何用哈希",
                "content": (
                    "边遍历边建哈希表 seen = {值: 下标}。对当前 x，先查 target - x 是否已在 "
                    "seen 中：在就说明配对的另一个数之前出现过，直接返回两个下标；不在就把 x "
                    "存入 seen 继续。一次遍历、O(n) 时间，避免了 O(n^2) 的双重循环。"
                ),
                "code": {
                    Language.PYTHON: (
                        "seen = {}\n"
                        "for i, x in enumerate(nums):\n"
                        "    if target - x in seen:\n"
                        "        return [seen[target - x], i]\n"
                        "    seen[x] = i\n"
                    ),
                },
            },
        ],
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
                "content": (
                    "seen = {}                      # 值 -> 下标\n"
                    "for i, x in enumerate(nums):\n"
                    "    if target - x in seen:      # 配对的数之前出现过\n"
                    "        return [seen[target - x], i]\n"
                    "    seen[x] = i                 # 记录当前值的下标"
                ),
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
        "knowledge_tips": [
            {
                "title": "什么是动态规划（DP）",
                "content": (
                    "动态规划把大问题拆成「重叠的子问题」，先解小的、用结果推大的，避免重复计算。"
                    "三要素：① 状态（dp[i] 表示什么）② 转移方程（dp[i] 由哪些更小的状态得来）"
                    "③ 边界（最小状态的初值）。"
                ),
            },
            {
                "title": "滚动变量优化空间",
                "content": (
                    "当 dp[i] 只依赖前面固定的几个状态（如本题只用 dp[i-1]、dp[i-2]）时，"
                    "不必开整个数组，用几个变量「滚动」即可把空间从 O(n) 降到 O(1)。"
                ),
                "code": {
                    Language.PYTHON: (
                        "a, b = 1, 1          # f(0)=1, f(1)=1\n"
                        "for _ in range(n - 1):\n"
                        "    a, b = b, a + b  # 同时更新，滚动前进\n"
                        "return b\n"
                    ),
                },
            },
            {
                "title": "本题状态与转移",
                "content": (
                    "到达第 n 阶，最后一步要么从 n-1 跨 1 阶、要么从 n-2 跨 2 阶上来，"
                    "故 f(n)=f(n-1)+f(n-2)，边界 f(1)=1、f(2)=2。本质就是斐波那契数列。"
                ),
            },
        ],
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
            {
                "level": 3,
                "content": (
                    "a, b = 1, 1              # f(1), f(2)\n"
                    "重复 n - 1 次:\n"
                    "    a, b = b, a + b      # 滚动前进\n"
                    "返回 b"
                ),
            },
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
