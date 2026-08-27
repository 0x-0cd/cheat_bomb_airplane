import random

from entities.enums import Block
from entities.solution import Solution
from strategies.common import head_count_matrix, pick_max_positions, run_benchmark
from utils import coordinates_to_str, str_to_coordinates
from utils.constants import direction_map


def _select_random(matrix, ctx):
    """随机选择法：在计数最大的候选位置中随机选一个。"""
    positions = pick_max_positions(matrix)
    return random.choice(positions)


def solve(sol: Solution):
    """随机选择法（交互模式）：推荐最可能是机头的位置，等待用户反馈。"""
    while True:
        matrix = head_count_matrix(sol)
        selected = _select_random(matrix, {})
        print(f"最可能是head的位置：{coordinates_to_str(selected)}")
        s, t = (
            input("请输入下一个选择的坐标，以及该坐标的类型(类型为head, body, blank)：")
            .strip()
            .split()
        )
        co = str_to_coordinates(s)
        sol.filter_pos(co, direction_map[t])
        if len(sol.confirmed_heads) == 3:
            print("恭喜你，获胜了！")
            break


def bench_mark(t: int):
    """解法基准测试：t 次随机局面的平均/最大/最小步数与方差。"""
    run_benchmark(t, _select_random)
