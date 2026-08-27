import os
from multiprocessing import cpu_count
from typing import Any, List, Optional, Tuple

import numpy as np

from entities.enums import Block
from utils.generator import generate_space, shape_signature


class Solution:
    """解集管理：numpy 向量化存储 + 机头计数矩阵增量维护。

    - _space: shape (N, 100) 的 uint8 数组，每行是一个合法布局，
      值为 Block 枚举的数值（0=Head, 1=Body, 2=Blank）
    - _head_count: shape (10, 10) 的 int64 矩阵，记录当前解集中每个格子
      作为机头出现的布局数。filter_pos 时增量更新，避免全量重扫。
    """

    def __init__(self, silent_mode: bool = False):
        self._space: np.ndarray = np.empty((0, 100), dtype=np.uint8)
        self._counts: np.ndarray = np.zeros((3, 10, 10), dtype=np.int64)
        self.confirmed_heads: List[Tuple[int, int]] = []
        self.guessed: List[Tuple[int, int]] = []

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

        # 三分类计数张量：counts[k][x][y] = 解集中 (x,y) 格为 k 类的布局数
        # k: 0=Head, 1=Body, 2=Blank（向量化一次计算，毫秒级）
        for k in (Block.Head.value, Block.Body.value, Block.Blank.value):
            self._counts[k] = (
                (self._space == k).sum(axis=0).reshape(10, 10)
            )

    @property
    def head_counts(self) -> np.ndarray:
        """当前解集中每个格子是机头的布局数矩阵（副本，避免外部误改）"""
        return self._counts[Block.Head.value].copy()

    @property
    def counts(self) -> np.ndarray:
        """三分类计数张量 (3, 10, 10) 副本：counts[k][x][y] = (x,y) 格为 k 类的布局数"""
        return self._counts.copy()

    def __save_cache(self, silent_mode: bool = False):
        """将解集写入带形状签名的 .npy 缓存文件"""
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        os.makedirs(cache_dir, exist_ok=True)
        np.save(self.__cache_path(), self._space)
        if not silent_mode:
            print(f"缓存文件保存成功，共 {len(self._space)} 条数据")

    def __cache_path(self) -> str:
        """缓存文件路径：文件名含形状签名，改形状/网格后自动失效"""
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        return os.path.join(cache_dir, f"cached_data_{shape_signature()}.npy")

    def __load_cache(self) -> bool:
        """加载当前形状签名对应的缓存；不存在则重新生成（约几秒）"""
        path = self.__cache_path()
        if not os.path.exists(path):
            return False
        try:
            arr = np.load(path)
            if arr.size > 0 and arr.ndim == 2:
                self._space = arr.astype(np.uint8)
                return True
        except Exception as e:
            print(f"加载 .npy 缓存失败：{e}")
        return False

    def __init_space(self):
        """用位运算生成器生成全部合法布局（形状定义在 airplane_offset）"""
        self._space = generate_space(10, 10)

    def get_len(self) -> int:
        return len(self._space)

    def determined_heads(self) -> Optional[List[Tuple[int, int]]]:
        """若机头位置已被推断确定，返回全部 3 个机头位置；否则返回 None。

        剩余候选机头格数 == 剩余机头数时，候选格即剩余机头：
        每个存活布局恰好有 remaining 个机头且都必须落在候选集内，
        因此所有存活布局共享同一组机头位置——无需再猜即可确定。
        """
        remaining = 3 - len(self.confirmed_heads)
        if remaining == 0:
            return list(self.confirmed_heads)
        mask = self.head_counts > 0
        for x, y in self.confirmed_heads:
            mask[x, y] = False
        if int(mask.sum()) != remaining:
            return None
        xs, ys = np.nonzero(mask)
        heads = list(self.confirmed_heads)
        heads.extend((int(x), int(y)) for x, y in zip(xs, ys))
        return sorted(heads)

    def filter_pos(self, pos: tuple, block_type: Block):
        """根据输入坐标和块类型过滤解集，并增量维护机头计数矩阵。

        只对被剪掉的布局回减机头贡献，不再全量重扫。
        """
        x, y = pos
        idx = x * 10 + y
        keep = self._space[:, idx] == block_type.value
        removed = self._space[~keep]
        if len(removed) > 0:
            # 增量更新三分类计数：对被剪掉的布局回减各类贡献
            for k in (Block.Head.value, Block.Body.value, Block.Blank.value):
                self._counts[k] -= (removed == k).sum(axis=0).reshape(10, 10)
        self._space = self._space[keep]
        self.guessed.append((x, y))
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
