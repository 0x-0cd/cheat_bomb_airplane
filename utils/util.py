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
