from entities.enums import Direction
from entities.playground import Playground


def coordinates_to_str(coordinates: tuple[int, int]) -> str:
    """
    将数字坐标（程序中的list下标）转换为字符串坐标

    e.g. (0, 0) -> "A10" | (1, 2) -> "C9" | (9, 4) -> "E1"
    """
    x, y = coordinates
    row = 10 - x
    col = chr(65 + y)
    return f"{col}{row}"


def str_to_coordinates(coordinates: str) -> tuple[int, int]:
    """
    将字符串坐标转换为数字坐标（程序中的list下标）,支持输入小写字母

    e.g. "A10" -> (0, 0)
    e.g. "C9" -> (1, 2)
    e.g. "E1" -> (9, 4)
    """
    coordinates = coordinates.upper()
    row = int(coordinates[1:])
    col = ord(coordinates[0]) - 65
    return (10 - row, col)


def calc_res_worker(args: tuple[Direction, Direction, Direction]):
    """计算一组方向组合下的所有合法布局"""
    dir_1, dir_2, dir_3 = args
    pg = Playground()
    results = []

    for pos_1 in range(100):
        x_1 = pos_1 // 10
        y_1 = pos_1 % 10
        if not pg.detect((x_1, y_1), dir_1):
            continue
        for pos_2 in range(pos_1, 100):
            x_2 = pos_2 // 10
            y_2 = pos_2 % 10
            if not pg.detect((x_2, y_2), dir_2):
                continue
            for pos_3 in range(pos_2, 100):
                x_3 = pos_3 // 10
                y_3 = pos_3 % 10
                if not pg.detect((x_3, y_3), dir_3):
                    continue

                # 放置飞机1
                pg.put_plane((x_1, y_1), dir_1)

                # 放置飞机2
                if not pg.detect((x_2, y_2), dir_2):
                    pg.flush()
                    continue
                pg.put_plane((x_2, y_2), dir_2)

                # 放置飞机3
                if not pg.detect((x_3, y_3), dir_3):
                    pg.flush()
                    continue
                pg.put_plane((x_3, y_3), dir_3)

                # 收集结果
                results.append(pg.snapshot())
                pg.flush()
    return results


if __name__ == "__main__":
    # for x in range(10):
    #     for y in range(10):
    #         print(coordinates_to_str((x, y)), end=" ")
    #     print()

    # for x in range(10):
    #     for y in range(10):
    #         print(str_to_coordinates(coordinates_to_str((x, y))), end=" ")
    #     print()

    res = calc_res_worker((Direction.Right, Direction.Down, Direction.Left))
    print(f"飞机方向：右下左， 共 {len(res)} 种合法布局")
