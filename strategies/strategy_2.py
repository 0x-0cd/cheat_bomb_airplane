from entities.solution import Solution
from strategies.common import head_count_matrix, pick_max_positions, run_benchmark
from utils import coordinates_to_str, str_to_coordinates
from utils.constants import direction_map


def manhattan_distance(pos1, pos2):
    """两个坐标的曼哈顿距离。"""
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def _select_farthest(sol: Solution, ctx):
    """最远曼哈顿距离法：计数最大的候选中，选离上一次选择最远的。"""
    matrix = head_count_matrix(sol)
    positions = pick_max_positions(matrix)
    previous = ctx.get("previous_pos")
    if previous is None:
        return positions[0]
    return max(positions, key=lambda p: manhattan_distance(previous, p))


def solve(sol: Solution):
    """最远曼哈顿距离法（交互模式）。"""
    previous_pos = None
    while True:
        selected = _select_farthest(sol, {"previous_pos": previous_pos})
        print(f"最可能是head的位置：{coordinates_to_str(selected)}")
        s, t = (
            input("请输入下一个选择的坐标，以及该坐标的类型(类型为head, body, blank)：")
            .strip()
            .split()
        )
        co = str_to_coordinates(s)
        previous_pos = co
        sol.filter_pos(co, direction_map[t])
        if len(sol.confirmed_heads) == 3:
            print("恭喜你，获胜了！")
            break


def bench_mark(t: int):
    """解法基准测试：t 次随机局面的平均/最大/最小步数与方差。"""
    run_benchmark(t, _select_farthest)
