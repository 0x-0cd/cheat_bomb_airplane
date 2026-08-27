import os
import pickle
from multiprocessing import Pool, cpu_count
from typing import Any, List, Tuple

import numpy as np

from entities.enums import Direction, Block
from utils import calc_res_worker


class Solution:
    """解集管理：numpy 向量化存储 + 机头计数矩阵增量维护。

    - _space: shape (N, 100) 的 uint8 数组，每行是一个合法布局，
      值为 Block 枚举的数值（0=Head, 1=Body, 2=Blank）
    - _head_count: shape (10, 10) 的 int64 矩阵，记录当前解集中每个格子
      作为机头出现的布局数。filter_pos 时增量更新，避免全量重扫。
    """

    def __init__(self, silent_mode: bool = False):
        self._space: np.ndarray = np.empty((0, 100), dtype=np.uint8)
        self._head_count: np.ndarray = np.zeros((10, 10), dtype=np.int64)
        self.confirmed_heads: List[Tuple[int, int]] = []

        if not self.__load_cache():
            if not silent_mode:
                print("缓存文件加载失败，开始初始化解集，该过程可能需要一些时间")
                print(f"【使用 {cpu_count()} 个CPU核心】")
            self.__init_space()
            self.__save_cache(silent_mode)
        else:
            if not silent_mode:
                print("从缓存文件加载解集成功！")

        if not silent_mode:
            print(f"解集初始化完成，共 {len(self._space)} 种合法布局")

        # 完整解集的机头计数矩阵（向量化一次计算，毫秒级）
        self._head_count = (
            (self._space == Block.Head.value).sum(axis=0).reshape(10, 10).astype(np.int64)
        )

    @property
    def head_counts(self) -> np.ndarray:
        """当前解集中每个格子是机头的布局数矩阵（副本，避免外部误改）"""
        return self._head_count.copy()

    def __save_cache(self, silent_mode: bool = False):
        """将解集写入 .npy 缓存文件"""
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        os.makedirs(cache_dir, exist_ok=True)
        np.save(os.path.join(cache_dir, "cached_data.npy"), self._space)
        if not silent_mode:
            print(f"缓存文件保存成功，共 {len(self._space)} 条数据")

    def __load_cache(self) -> bool:
        """优先加载 .npy 缓存；不存在时迁移旧 pickle 缓存（一次性）"""
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        npy_path = os.path.join(cache_dir, "cached_data.npy")
        if os.path.exists(npy_path):
            try:
                arr = np.load(npy_path)
                if arr.size > 0 and arr.ndim == 2:
                    self._space = arr.astype(np.uint8)
                    return True
            except Exception as e:
                print(f"加载 .npy 缓存失败：{e}")

        pkl_path = os.path.join(cache_dir, "cached_data.pkl")
        if os.path.exists(pkl_path):
            try:
                with open(pkl_path, "rb") as f:
                    old = pickle.load(f)
                self._space = np.array(
                    [
                        [cell.value for row in board for cell in row]
                        for board in old
                    ],
                    dtype=np.uint8,
                )
                if self._space.size > 0:
                    self.__save_cache(silent_mode=True)
                    return True
            except Exception as e:
                print(f"迁移旧 pickle 缓存失败：{e}")
        return False

    def __init_space(self):
        """以方向组合为任务并行生成全部合法布局"""
        tasks = [
            (dir_1, dir_2, dir_3)
            for dir_1 in Direction
            for dir_2 in Direction
            for dir_3 in Direction
        ]
        with Pool() as pool:
            results = pool.map(calc_res_worker, tasks)
        rows = []
        for result in results:
            rows.extend(result)
        self._space = np.array(
            [
                [cell.value for row in board for cell in row]
                for board in rows
            ],
            dtype=np.uint8,
        )

    def get_len(self) -> int:
        return len(self._space)

    def filter_pos(self, pos: tuple, block_type: Block):
        """根据输入坐标和块类型过滤解集，并增量维护机头计数矩阵。

        只对被剪掉的布局回减机头贡献，不再全量重扫。
        """
        x, y = pos
        idx = x * 10 + y
        keep = self._space[:, idx] == block_type.value
        removed = self._space[~keep]
        if len(removed) > 0:
            removed_head = (removed == Block.Head.value).sum(axis=0).reshape(10, 10)
            self._head_count -= removed_head
        self._space = self._space[keep]
        if block_type == Block.Head:
            self.confirmed_heads.append((x, y))

    def statistics(self, condition: Any) -> int:
        """基于自定义条件函数统计解集中符合条件的布局数量。

        condition 接收一行布局（100 个 Block 元素的列表），返回 bool。
        """
        res = 0
        for row in self._space:
            if condition([Block(v) for v in row]):
                res += 1
        return res


if __name__ == "__main__":
    sol = Solution()

    def condition(s):
        return s[3][4] != Block.Head

    print(f"初始解集大小为 {sol.get_len()}")
    print(f"初始解集中 (3, 4) 不是机头的布局数量为 {sol.statistics(condition)}")

    sol.filter_pos((3, 4), Block.Head)
    print(f"过滤后解集大小为 {sol.get_len()}")
