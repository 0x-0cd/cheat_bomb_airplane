import random
from multiprocessing import Pool, cpu_count
from statistics import variance
from typing import List, Tuple
from entities.enums import Block
from entities.solution import Solution
from utils import coordinates_to_str, str_to_coordinates
from utils.constants import direction_map


def solve(sol: Solution):
    """
    曼哈顿距离选择法：
    1. 统计解集中最可能是head的位置
    2. 如果最可能是head的位置有多个，选择与前一次选择的区块的曼哈顿距离最远的备选区块
    3. 初始状态下，选择第一个备选格
    """
    # 记录前一次选择的位置
    previous_pos = None

    while True:
        # 计算解集中每个位置是head的次数
        head_matrix = calc_head_time(sol)

        # 过滤掉已经炸出来的head位置
        for x, y in sol.confirmed_heads:
            head_matrix[x][y] = 0

        # 选择最可能是head的位置之一
        max_count = max(max(row) for row in head_matrix)
        max_positions = [
            (i, j)
            for i in range(10)
            for j in range(10)
            if head_matrix[i][j] == max_count
        ]

        # 选择位置的逻辑
        if previous_pos is None:
            # 初始状态，选择第一个备选格
            selected_pos = max_positions[0]
        else:
            # 计算每个位置与前一次选择的曼哈顿距离
            max_distance = -1
            selected_pos = max_positions[0]

            for pos in max_positions:
                distance = manhattan_distance(previous_pos, pos)
                if distance > max_distance:
                    max_distance = distance
                    selected_pos = pos

        # 输出选择的位置
        print(f"最可能是head的位置：{coordinates_to_str(selected_pos)}")
        s, t = (
            input("请输入下一个选择的坐标，以及该坐标的类型(类型为head, body, blank)：")
            .strip()
            .split()
        )
        co = str_to_coordinates(s)
        # 更新前一次选择的位置
        previous_pos = co
        sol.filter_pos(co, direction_map[t])
        if len(sol.confirmed_heads) == 3:
            print("恭喜你，获胜了！")
            break


def manhattan_distance(pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
    """
    计算两个位置之间的曼哈顿距离
    """
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


def calc_head_time_worker(
    args: Tuple[List, List[Tuple[int, int]]],
) -> List[Tuple[int, int, int]]:
    """
    工作函数：计算指定位置列表在给定解子集上是head的次数
    """
    space_subset, positions = args
    results = []
    for i, j in positions:
        count = 0
        for s in space_subset:
            if s[i][j] == Block.Head:
                count += 1
        results.append((i, j, count))
    return results


def calc_head_time(sol: Solution) -> List[List[int]]:
    """
    计算解集中每个位置是head的次数，返回一个10x10的矩阵
    使用多进程并行计算以提高性能
    """
    # 初始化结果矩阵
    time = [[0 for _ in range(10)] for _ in range(10)]

    # 获取解集
    space = sol._space

    # 获取CPU核心数
    num_cores = cpu_count()

    # 计算每个核心处理的解数量
    space_size = len(space)
    space_per_core = space_size // num_cores
    if space_size % num_cores != 0:
        space_per_core += 1

    # 生成所有需要计算的位置
    all_positions = [(i, j) for i in range(10) for j in range(10)]

    # 分割解集和位置，为每个核心分配任务
    tasks = []
    for i in range(0, space_size, space_per_core):
        end = min(i + space_per_core, space_size)
        space_subset = space[i:end]
        tasks.append((space_subset, all_positions))

    # 使用多进程并行计算
    with Pool() as pool:
        results_list = pool.map(calc_head_time_worker, tasks)

    # 合并结果
    for results in results_list:
        for i, j, count in results:
            time[i][j] += count

    return time


def bench_mark(t: int):
    """
    解法基准测试

    t - 测试次数
    """
    # 测试结果集合
    results = []

    # 测试循环
    for i in range(t):
        # 初始化解集
        sol = Solution(silent_mode=True)

        # 随机选一个局面作为答案
        ans = random.choice(sol._space)

        step = 0
        previous_pos = None
        while len(sol.confirmed_heads) < 3:
            step += 1

            # 计算解集中每个位置是head的次数
            head_matrix = calc_head_time(sol)

            # 过滤掉已经炸出来的head位置
            for x, y in sol.confirmed_heads:
                head_matrix[x][y] = 0

            # 选择最可能是head的位置之一
            max_count = max(max(row) for row in head_matrix)
            max_positions = [
                (i, j)
                for i in range(10)
                for j in range(10)
                if head_matrix[i][j] == max_count
            ]

            # 选择位置的逻辑
            if previous_pos is None:
                # 初始状态，选择第一个备选格
                max_co = max_positions[0]
            else:
                # 计算每个位置与前一次选择的曼哈顿距离
                max_distance = -1
                max_co = max_positions[0]

                for pos in max_positions:
                    distance = manhattan_distance(previous_pos, pos)
                    if distance > max_distance:
                        max_distance = distance
                        max_co = pos

            block_type = ans[max_co[0]][max_co[1]]
            # 更新前一次选择的位置
            previous_pos = max_co
            sol.filter_pos(max_co, block_type)
            if len(sol.confirmed_heads) == 3:
                results.append(step)
                break

    # 输出基准测试结果
    print(f"测试次数：{t}")
    print(f"平均步数：{sum(results) / t}")
    print(f"最大步数：{max(results)}")
    print(f"最小步数：{min(results)}")
    print(f"方差：{variance(results)}")
