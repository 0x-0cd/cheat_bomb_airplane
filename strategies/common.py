"""策略公共模块：机头计数矩阵读取与基准测试骨架。

strategy_1 / strategy_2 共用的部分收敛到这里：
- head_count_matrix: 从 Solution 取计数矩阵（已确认机头置 0）
- pick_max_positions: 找出计数最大的所有候选位置
- run_benchmark: 通用基准测试循环
"""
import random
from statistics import variance
from typing import Callable, Dict, List, Tuple

import numpy as np

from entities.enums import Block
from entities.solution import Solution


def head_count_matrix(sol: Solution) -> np.ndarray:
    """当前解集的机头计数矩阵副本，已确认的机头位置置 0。"""
    matrix = sol.head_counts
    for x, y in sol.confirmed_heads:
        matrix[x, y] = 0
    return matrix


def pick_max_positions(matrix: np.ndarray) -> List[Tuple[int, int]]:
    """返回计数最大的所有位置，保持 (i, j) 行主序枚举顺序。"""
    max_count = int(matrix.max())
    return [
        (i, j)
        for i in range(10)
        for j in range(10)
        if matrix[i, j] == max_count
    ]


def run_benchmark(
    t: int,
    select_fn: Callable[[np.ndarray, Dict], Tuple[int, int]],
) -> List[int]:
    """通用基准测试。

    select_fn(matrix, ctx) -> (x, y)：根据计数矩阵和上下文选择下一格。
    ctx 由调用方约定（如策略 2 用它记录 previous_pos）。
    返回每局的步数列表。
    """
    results = []
    for _ in range(t):
        sol = Solution(silent_mode=True)
        ans = sol._space[random.randrange(len(sol._space))]
        ctx: Dict = {}
        step = 0
        while len(sol.confirmed_heads) < 3:
            step += 1
            matrix = head_count_matrix(sol)
            pos = select_fn(matrix, ctx)
            block_type = Block(int(ans[pos[0] * 10 + pos[1]]))
            ctx["previous_pos"] = pos
            sol.filter_pos(pos, block_type)
        results.append(step)

    print(f"测试次数：{t}")
    print(f"平均步数：{sum(results) / t}")
    print(f"最大步数：{max(results)}")
    print(f"最小步数：{min(results)}")
    print(f"方差：{variance(results)}")
    return results
