"""三策略全量对比模拟。

遍历解集全部布局，分别用策略1/2/3 模拟完整对局，统计步数分布：
平均 / 最优 / 最差 / p50 / p95 / 方差。

用法（在项目根目录运行）：
    python3 bench_compare.py              # 全部 3 个策略 × 全部 66816 布局
    python3 bench_compare.py 1000         # 只跑前 1000 个布局（快速验证）
    python3 bench_compare.py 1000 3       # 只跑策略3（前 1000 布局）

说明：
- 策略1（随机选择）含随机性：每个布局使用独立固定随机流（seed = 1000 + 布局索引），
  结果可复现。策略2/3 为确定性策略。
- 多进程并行，进程数 = CPU 核心数。全量 66816 布局在 Mac 上约几分钟。
"""
import os
import sys
import time
import random
import multiprocessing as mp

import numpy as np

sys.path.insert(0, os.getcwd())  # 项目根目录

from entities.solution import Solution
from entities.enums import Block
from strategies.strategy_1 import _select_random
from strategies.strategy_2 import _select_farthest
from strategies.strategy_3 import _select_ig

# 策略编号 -> (名称, 选择函数, 是否含随机性)
STRATEGIES = {
    1: ("策略1 随机选择法", _select_random, True),
    2: ("策略2 最远曼哈顿距离法", _select_farthest, False),
    3: ("策略3 期望信息增益法", _select_ig, False),
}

SEED = 1000


def simulate(sol, base_space, base_counts, ans, select_fn, use_random, layout_idx):
    """对一个固定答案布局跑完整决策，返回步数。"""
    sol._space = base_space          # filter_pos 是 rebind，不原地改 base_space
    sol._counts = base_counts.copy()  # counts 是原地减法，必须重置
    sol.guessed = []
    sol.confirmed_heads = []
    if use_random:
        random.seed(SEED + layout_idx)  # 每布局独立可复现随机流
    step = 0
    while len(sol.confirmed_heads) < 3:
        step += 1
        pos = select_fn(sol, {})
        bt = Block(int(ans[pos[0] * 10 + pos[1]]))
        sol.filter_pos(pos, bt)
    return step


def worker(args):
    start, end, strat_ids = args
    sol = Solution(silent_mode=True)
    base_space = sol._space
    base_counts = sol._counts.copy()
    results = {sid: [] for sid in strat_ids}
    for i in range(start, end):
        ans = base_space[i]
        for sid in strat_ids:
            _, select_fn, use_random = STRATEGIES[sid]
            results[sid].append(simulate(sol, base_space, base_counts, ans, select_fn, use_random, i))
    return results


def main():
    n_total = 66816
    args = sys.argv[1:]
    n = int(args[0]) if args else n_total
    strat_ids = [int(x) for x in args[1:]] if len(args) > 1 else [1, 2, 3]
    n = min(n, n_total)
    for sid in strat_ids:
        if sid not in STRATEGIES:
            print(f"未知策略编号: {sid}（可用: {list(STRATEGIES)}）")
            sys.exit(1)

    t0 = time.time()
    nproc = mp.cpu_count()
    chunk = (n + nproc - 1) // nproc
    batches = [(i, min(i + chunk, n), strat_ids) for i in range(0, n, chunk)]
    with mp.Pool(nproc) as pool:
        all_results = pool.map(worker, batches)

    steps = {sid: [] for sid in strat_ids}
    for r in all_results:
        for sid in strat_ids:
            steps[sid].extend(r[sid])

    print(f"模拟布局数: {n}（总解集 {n_total}）  耗时 {time.time() - t0:.1f}s")
    print()
    header = f"{'策略':<22} {'平均':>7} {'最优':>5} {'最差':>5} {'p50':>6} {'p95':>6} {'方差':>8}"
    print(header)
    print("-" * len(header))
    for sid in strat_ids:
        name, _, _ = STRATEGIES[sid]
        arr = np.array(steps[sid], dtype=np.int64)
        print(
            f"{name:<22} {arr.mean():>7.3f} {arr.min():>5} {arr.max():>5} "
            f"{np.percentile(arr, 50):>6.1f} {np.percentile(arr, 95):>6.1f} {arr.var():>8.3f}"
        )


if __name__ == "__main__":
    main()
