# 炸弹飞机游戏辅助工具

## 项目介绍

这是一个用于「[炸飞机](https://game.hullqin.cn/zfj)」游戏的辅助工具，通过**期望信息增益分析**和**逻辑推断**，帮助玩家快速找到游戏中的飞机位置。项目使用 Python + numpy 向量化实现，解集生成采用位运算，提供多种策略并通过全量基准测试量化对比，目标是最大化猜测效率（平均 11.95 步找齐 3 个机头）。

## 游戏规则

「炸弹飞机」是一种经典的策略游戏，游戏规则如下：

1. 游戏在一个10x10的网格上进行
2. 玩家需要在网格中隐藏3架飞机
3. 每架飞机由1个机头和9个机身组成
4. 玩家通过猜测坐标来寻找对方的飞机
5. 首先找到对方所有3个机头的玩家获胜

## 项目结构

```
cheat_bomb_airplane/
├── entities/           # 核心实体类
│   ├── __init__.py
│   ├── enums.py        # 枚举定义
│   ├── playground.py   # 游戏场地
│   └── solution.py     # 解集管理
├── strategies/          # 策略实现
│   ├── __init__.py
│   ├── common.py       # 公共：机头计数矩阵读取 + 基准测试骨架
│   ├── strategy_1.py   # 策略1：随机选择法
│   ├── strategy_2.py   # 策略2：最远曼哈顿距离法
│   └── strategy_3.py   # 策略3：期望信息增益法（推荐）
├── utils/              # 工具函数
│   ├── __init__.py
│   ├── constants.py    # 常量（含飞机形状唯一定义 airplane_offset）
│   ├── generator.py    # 位运算解集生成器（形状自动推导）
│   └── util.py         # 坐标转换工具
├── .gitignore
├── .python-version
├── LICENSE
├── README.md           # 项目说明
├── main.py             # 入口文件
├── bench_compare.py    # 三策略全量对比脚本（支持提前终止 -e）
├── pyproject.toml      # 项目配置
└── uv.lock             # 依赖锁文件
```

## 核心功能

### 1. 解集生成

- 预计算所有合法的飞机布局（66816 种）
- 使用位运算生成器：飞机形状由 `airplane_offset` 唯一定义，越界/重叠检测用 100-bit 掩码位与，生成仅需数秒
- 缓存机制：解集缓存为带形状签名的 `.npy` 文件（`cache/cached_data_<签名>.npy`），改形状/网格后自动失效重新生成

### 2. 智能策略

- 策略1（随机选择法）：机头概率最大的位置中随机选
- 策略2（最远曼哈顿距离法）：机头概率最大的位置中选离上次最远的
- 策略3（期望信息增益法，推荐）：选使反馈后解集期望剩余最小的格子，
  主动探索高区分度位置而非只追命中概率

### 3. 提前终止（推断确定）

`Solution.determined_heads()`：当**剩余候选机头格数 == 剩余机头数**时，机头位置已被逻辑推断确定（鸽笼原理：每个存活布局的剩余机头必须落在候选集内，候选数恰好等于配额 → 无摇摆空间），程序直接提示获胜，无需再猜。

这是对"目标失配"的修正：游戏只需确定机头，不需要区分所有布局（尾部 body 布局差异对找机头无意义）。实测平均步数 **13.06 → 11.95**（-1.1 步，方差 4.71 → 3.02）。

### 4. 策略对比（全量 66816 布局实测）

| 策略 | 平均 | 最优 | 最差 | p50 | p95 | 方差 |
|:-----|:----:|:----:|:----:|:---:|:---:|:----:|
| 策略1 随机选择¹ | ~14.5 | 3 | 23 | 14 | 19 | ~11 |
| 策略2 最远曼哈顿 | 14.30 | 3 | 28 | 14 | 20 | 11.10 |
| 策略3 期望信息增益 | 13.06 | 3 | 20 | 13 | 16 | 4.71 |
| **策略3 + 提前终止** | **11.95** | **3** | **17** | **12** | **14** | **3.02** |

¹ 策略1 含随机性，数据为 bench 100 次抽样；其余为全量 66816 布局逐局模拟（M4 实测，可复现）。

策略3 + 提前终止平均最少且方差最小（对抗场景更稳），为推荐配置。

### 5. 基准测试

- 评估策略的平均猜测次数
- 统计最大、最小猜测次数和方差
- 帮助优化策略性能

## 安装和使用

### 安装依赖

```bash
# 使用uv安装依赖
uv sync
```

### 运行项目

```bash
# 运行基准测试（默认100次）
uv run main.py
```

### 交互式使用

1. 运行交互式模式后，程序每步推荐"最可能是head的位置"（如 `F5`）
2. 输入你选择的坐标和该位置的类型（head/body/blank）
3. 程序根据反馈更新解集并继续推荐
4. 当机头位置可推断确定时（提前终止），程序直接打印全部 3 个机头位置并宣布获胜

```bash
python3 -c "from entities.solution import Solution; import strategies.strategy_3 as s3; s3.solve(Solution())"
```

## 技术实现

### numpy 向量化与增量维护

项目使用 numpy 数组存储解集（`(N, 100)` uint8），核心计算全部向量化：

- 机头计数矩阵：一次向量化求和得到每个格子是机头的布局数
- 过滤解集：布尔掩码向量化过滤，并对计数矩阵增量回减被剪布局的贡献（不再全量重扫）
- 单次概率统计从全量 O(N×100) 降为 O(1) 查矩阵

### 缓存机制

- 解集缓存为 numpy `.npy` 文件，文件名含形状签名（`airplane_offset` + 网格尺寸的 md5）
- 改飞机形状或网格大小后缓存自动失效，重新生成仅需数秒
- 首次运行后，后续启动从缓存加载，加载仅需几十毫秒

### 信息增益算法（策略3）

1. 维护三分类计数张量 `counts[k][x][y]`（Head/Body/Blank 各格的布局数，filter 时增量更新，查询 O(1)）
2. 每步选择使反馈后解集期望剩余 `Σ|S_r|²/|S|` 最小的格子（即最大化信息增益）
3. 已猜过的格子排除；分数相同时优先机头概率更高的格子
4. 机头可推断确定（`determined_heads`）时提前结束

> 注：经实验验证，真熵目标（-Σp·logp）、反馈类型加权、多步前瞻等改进均无收益（甚至略差），纯信息增益贪心已接近该问题的最优解。

## 策略评估

### 单策略基准（随机抽样）

```bash
python3 -c "import strategies.strategy_3 as s3; s3.bench_mark(100)"
```

输出：测试次数 / 平均步数 / 最大步数 / 最小步数 / 方差。

### 全量对比（推荐）

遍历全部 66816 布局逐局模拟，统计平均 / 最优 / 最差 / p50 / p95 / 方差，多进程并行：

```bash
python3 bench_compare.py                # 三策略全量对比
python3 bench_compare.py 66816 3 -e     # 策略3 + 提前终止
python3 bench_compare.py 1000           # 快速验证（前 1000 布局）
```

策略1 含随机性，脚本为每个布局分配独立固定随机流（可复现）；策略2/3 为确定性策略，跨机器结果完全一致。

## 扩展和定制

### 添加新策略

在 `strategies` 目录创建新策略文件（如 `strategy_4.py`），实现选择函数并复用公共基准框架：

```python
from entities.solution import Solution
from strategies.common import run_benchmark


def _select_my(sol: Solution, ctx):
    # 根据解集选择下一个猜测位置，返回 (x, y)
    # 可用信息：sol.counts（三分类计数张量）、sol.head_counts、
    #           sol.guessed / sol.confirmed_heads；ctx 保存跨步状态
    ...


def solve(sol: Solution):
    # 交互模式（参考 strategy_3.py）

def bench_mark(t: int):
    run_benchmark(t, _select_my)
```

选择函数签名 `select_fn(sol, ctx) -> (x, y)`，`ctx` 可保存跨步状态（如策略2 的 previous_pos）。基准测试自动复用 `run_benchmark`，全量对比直接加到 `bench_compare.py` 的 `STRATEGIES` 字典即可。

### 自定义评估

使用`Solution.statistics`方法可以自定义评估函数：

```python
def condition(s):
    # 自定义条件函数
    return s[3][4] == Block.Head

count = sol.statistics(condition)
```

## 注意事项

1. 首次运行自动生成解集（位运算，约 6 秒），缓存在 `cache/cached_data_<形状签名>.npy`
2. 改飞机形状（`utils/constants.py` 的 `airplane_offset`）或网格大小后，缓存自动失效并重新生成
3. 项目要求 Python 3.13+，依赖 numpy（`uv sync` 安装）

## 许可证

本项目采用MIT许可证，详见LICENSE文件。
