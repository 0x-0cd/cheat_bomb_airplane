"""策略3：期望信息增益法（IG）。

每步选使「反馈后解集期望剩余」最小的格子：
    期望剩余(g) = (|S_Head|² + |S_Body|² + |S_Blank|²) / |S|

反馈把解集切成 Head/Body/Blank 三类，三类越均衡、每类越小，
信息增益越大。与策略 1/2 的「机头概率最大化」不同，IG 主动
探索高区分度的格子，避免在高概率区域反复扎堆。
"""
import numpy as np

from entities.enums import Block
from entities.solution import Solution
from strategies.common import run_benchmark
from utils import coordinates_to_str, str_to_coordinates
from utils.constants import direction_map


def _select_ig(sol: Solution, ctx):
    """IG 贪心：选期望剩余解集最小的未猜格子。

    分数 = Σ|S_r|²（除以 |S| 是常数不影响排序）。
    tie-break：分数相同时优先 head 概率更高的格（解集极小时快速收敛到机头）。
    """
    counts = sol.counts  # (3, 10, 10) 副本：counts[k][x][y] = 该格为 k 类的布局数
    scores = (counts.astype(np.int64) ** 2).sum(axis=0)  # (10, 10) Σc²
    # 已猜过的格子不再猜（解集缩小时平局分数会选中它们，必须排除）
    for x, y in sol.guessed:
        scores[x, y] = np.iinfo(np.int64).max
    # lexsort：主键 scores 升序，次键 -head 升序（head 降序）→ 平局优先机头
    order = np.lexsort((-counts[Block.Head.value].ravel(), scores.ravel()))
    idx = int(order[0])
    return (idx // 10, idx % 10)


def solve(sol: Solution):
    """期望信息增益法（交互模式）。"""
    while True:
        selected = _select_ig(sol, {})
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
    run_benchmark(t, _select_ig)
