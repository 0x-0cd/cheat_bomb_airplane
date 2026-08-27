"""位运算解集生成器。

飞机形状的唯一定义在 utils/constants.py 的 airplane_offset，
本模块从偏移表自动推导合法摆放（越界检查通用化，不手写边界），
因此换形状只需改偏移表一处，重新生成解集只需几秒。

编码约定：
- 网格 rows×cols，格子 idx = x*cols + y
- 一个摆放 = Python 大整数位掩码，bit i = 1 表示第 i 格被占用
- 一架飞机 = 机头掩码（1 bit）+ 完整掩码（机头 1 bit + 机身 9 bits）
- 三机布局合法 ⇔ 三架飞机的完整掩码两两位与为 0（重叠检测一次位与）
"""
import hashlib

import numpy as np

from entities.enums import Direction, Block
from utils.constants import airplane_offset


def shape_signature(rows: int = 10, cols: int = 10) -> str:
    """形状签名：由 airplane_offset + 网格尺寸计算。

    改飞机形状或网格大小后签名变化 → 缓存文件名变化 → 自动重新生成，
    避免加载旧形状的解集缓存。
    """
    raw = repr((rows, cols, [(d.name, airplane_offset[d]) for d in Direction]))
    return hashlib.md5(raw.encode()).hexdigest()[:8]


def _single_plane_masks(direction: Direction, rows: int, cols: int):
    """返回该方向所有合法单机摆放的 (head_bit, full_mask) 列表。

    越界检查直接从偏移表推导：任何一格落在网格外即非法。
    不依赖手写边界，所以任何形状/网格都能自动适配。
    """
    masks = []
    for x in range(rows):
        for y in range(cols):
            head_bit = x * cols + y
            bits = [head_bit]
            valid = True
            for dx, dy in airplane_offset[direction]:
                nx, ny = x + dx, y + dy
                if not (0 <= nx < rows and 0 <= ny < cols):
                    valid = False
                    break
                bits.append(nx * cols + ny)
            if valid:
                full_mask = 0
                for b in bits:
                    full_mask |= 1 << b
                masks.append((head_bit, full_mask))
    return masks


def _layout_to_row(head_bits, fulls, rows: int, cols: int) -> np.ndarray:
    """三架飞机的掩码 → 一行 (rows*cols,) uint8 布局。

    head_bits 是机头位置索引（如 34 表示 idx=34 格），不是掩码。
    """
    row = np.full(rows * cols, Block.Blank.value, dtype=np.uint8)
    for head_bit, full_mask in zip(head_bits, fulls):
        m = full_mask
        while m:
            bit = (m & -m).bit_length() - 1
            row[bit] = Block.Body.value
            m &= m - 1
        row[head_bit] = Block.Head.value
    return row


def generate_space(rows: int = 10, cols: int = 10) -> np.ndarray:
    """生成全部合法三机布局，返回 (N, rows*cols) 的 uint8 数组。

    保持与原实现相同的枚举语义：
    - 三架飞机按机头位置非严格递增（等价 pos_1 <= pos_2 <= pos_3）
    - 同一机头位置允许不同朝向（如机头同格、朝向不同）
    """
    dirs = list(Direction)
    candidates = {d: _single_plane_masks(d, rows, cols) for d in dirs}

    layouts = []
    append = layouts.append
    for d1 in dirs:
        c1 = candidates[d1]
        for d2 in dirs:
            c2 = candidates[d2]
            for d3 in dirs:
                c3 = candidates[d3]
                for h1, f1 in c1:
                    for h2, f2 in c2:
                        if h2 < h1 or (f1 & f2):
                            continue
                        combined = f1 | f2
                        for h3, f3 in c3:
                            if h3 < h2 or (combined & f3):
                                continue
                            append(_layout_to_row((h1, h2, h3), (f1, f2, f3), rows, cols))
    return np.array(layouts, dtype=np.uint8)


if __name__ == "__main__":
    import time

    t0 = time.time()
    space = generate_space()
    print(f"生成解集：{len(space)} 种布局，耗时 {time.time() - t0:.2f}s")
