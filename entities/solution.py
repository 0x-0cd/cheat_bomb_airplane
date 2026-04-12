import os
import pickle
from multiprocessing import Pool, cpu_count
from typing import Any
from entities.enums import Direction, Block
from utils import calc_res_worker


class Solution:
    def __init__(self):
        self.__space = []

        # 从缓存文件加载解集，如果失败则初始化解集，并保存到缓存文件
        if not self.__load_cache():
            print("缓存文件加载失败，开始初始化解集，该过程可能需要一些时间")
            print(f"【使用 {cpu_count()} 个CPU核心】")
            self.__init_space()
            self.__save_cache()
        else:
            print("从缓存文件加载解集成功！")

        print(f"解集初始化完成，共 {len(self.__space)} 种合法布局")

        # 记录已确认的机头位置
        self.confirmed_heads = []

    def __save_cache(self):
        """
        将 self.__space 写入到缓存文件（使用 pickle 序列化）
        """
        cache_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "cache", "cached_data.pkl"
        )

        # 确保缓存目录存在
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)

        with open(cache_file, "wb") as f:
            pickle.dump(self.__space, f)

        print(f"缓存文件保存成功，共 {len(self.__space)} 条数据")

    def __load_cache(self) -> bool:
        """
        从缓存文件加载解集（使用 pickle 反序列化）
        """
        cache_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "cache", "cached_data.pkl"
        )

        if not os.path.exists(cache_file):
            return False

        try:
            with open(cache_file, "rb") as f:
                self.__space = pickle.load(f)

            if len(self.__space) > 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"加载缓存文件失败：{e}")
            return False

    def __init_space(self):
        # 以方向组合为参数划分任务
        tasks = [
            (dir_1, dir_2, dir_3)
            for dir_1 in Direction
            for dir_2 in Direction
            for dir_3 in Direction
        ]

        # 使用多进程并行计算
        with Pool() as pool:
            results = pool.map(calc_res_worker, tasks)

        # 合并结果
        for result in results:
            self.__space.extend(result)

    def get_len(self):
        """
        返回当前解集大小
        """
        return len(self.__space)

    def filter_pos(self, pos: tuple, block_type: Block):
        """
        根据输入的坐标和块类型过滤解集，并记录已确认的机头位置

        e.g.

        该调用会过滤解集中 (3, 4) 不是机头的布局，并记录 (3, 4) 为已确认的机头位置
        ```
        filter_pos((3, 4), Block.Head)
        ```
        """
        x, y = pos

        # 过滤掉解空间中不是输入块类型的的位置布局
        self.__space = [s for s in self.__space if s[x][y] == block_type]

        # 记录已确认的机头位置
        if block_type == Block.Head:
            self.confirmed_heads.append((x, y))

    def statistics(self, condition: Any) -> int:
        """
        基于自定义的条件函数condition统计解集中符合条件的布局数量

        condition: 入参为解集中的一个布局，返回值为bool，True表示符合条件，False表示不符合条件

        e.g.
        统计解集中 (3, 4) 为机头的布局数量
        ```
        def condition(s):
            return s[3][4] == Block.Head
        ```
        """
        res = 0
        for s in self.__space:
            if condition(s):
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
