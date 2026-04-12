from enum import Enum


# 飞机头朝向枚举
class Direction(Enum):
    Up = 0
    Down = 1
    Left = 2
    Right = 3


# 方格类型枚举
class Block(Enum):
    Head = 0  # 机头
    Body = 1  # 机身
    Blank = 2  # 空
