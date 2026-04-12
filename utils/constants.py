from entities.enums import Block, Direction

# 方向字符串到枚举的映射
direction_map = {
    "head": Block.Head,
    "body": Block.Body,
    "blank": Block.Blank,
}

# 机身相对于机头的坐标偏移量
airplane_offset = {
    Direction.Up: [
        (1, -2),
        (1, -1),
        (1, 0),
        (1, 1),
        (1, 2),
        (2, 0),
        (3, -1),
        (3, 0),
        (3, 1),
    ],
    Direction.Down: [
        (-1, -2),
        (-1, -1),
        (-1, 0),
        (-1, 1),
        (-1, 2),
        (-2, 0),
        (-3, -1),
        (-3, 0),
        (-3, 1),
    ],
    Direction.Left: [
        (-2, 1),
        (-1, 1),
        (0, 1),
        (1, 1),
        (2, 1),
        (0, 2),
        (-1, 3),
        (0, 3),
        (1, 3),
    ],
    Direction.Right: [
        (-2, -1),
        (-1, -1),
        (0, -1),
        (1, -1),
        (2, -1),
        (0, -2),
        (-1, -3),
        (0, -3),
        (1, -3),
    ],
}
