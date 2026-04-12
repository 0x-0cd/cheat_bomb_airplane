import copy
from typing import List
from entities.enums import Direction, Block
from utils import airplane_offset


class Playground:
    def __init__(self):
        # 初始化盘面
        self.__playground = []
        for _ in range(10):
            self.__playground.append([Block.Blank] * 10)

    def __set_block(self, pos: tuple, block_type: Block):
        """
        单块更新，禁止外部调用
        """
        x, y = pos
        self.__playground[x][y] = block_type

    def _show(self):
        """
        展示盘面，用于调试
        """
        for line in self.__playground:
            for block in line:
                if block == Block.Blank:
                    print("☐", end=" ")
                elif block == Block.Body:
                    print("◼︎", end=" ")
                else:
                    print("☒", end=" ")
            print()

    def flush(self):
        """
        刷新盘面为全空
        """
        for i in range(10):
            for j in range(10):
                self.__set_block((i, j), Block.Blank)

    def detect(self, pos: tuple, direction: Direction) -> bool:
        """
        检测在指定位置和方向上是否允许放置飞机
        """

        x, y = pos

        # 排除一定会导致部分机身在盘面外的情况
        if direction == Direction.Up:
            if y < 2 or y > 7 or x > 6:
                return False
        elif direction == Direction.Down:
            if y < 2 or y > 7 or x < 3:
                return False
        elif direction == Direction.Left:
            if x < 2 or x > 7 or y > 6:
                return False
        else:
            if x < 2 or x > 7 or y < 3:
                return False

        # 排除机头和机身已经被占据的情况
        if self.__playground[x][y] != Block.Blank:
            return False
        for offset_x, offset_y in airplane_offset[direction]:
            if self.__playground[x + offset_x][y + offset_y] != Block.Blank:
                return False
        return True

    def put_plane(self, pos: tuple, direction: Direction):
        """
        放置飞机，更新盘面
        """
        if self.detect(pos, direction):
            self.__set_block(pos, Block.Head)
            x, y = pos
            for offset_x, offset_y in airplane_offset[direction]:
                self.__set_block((x + offset_x, y + offset_y), Block.Body)

    def snapshot(self) -> List[List[Block]]:
        """
        生成当前盘面的快照
        """
        return copy.deepcopy(self.__playground)


if __name__ == "__main__":
    pg = Playground()
    s = pg.put_plane((7, 0), Direction.Left)
    pg._show()
    print("--------------------")
    s = pg.put_plane((3, 3), Direction.Down)
    pg._show()
    print("--------------------")
    pg.flush()
    pg._show()
