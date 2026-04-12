from entities.solution import Solution
import strategies.strategy_1
import strategies.strategy_2


def main():
    sol = Solution()
    strategies.strategy_2.solve(sol)

    # print("【策略1】")
    # strategies.strategy_1.bench_mark(100)
    # print("【策略2】")
    # strategies.strategy_2.bench_mark(100)


if __name__ == "__main__":
    main()
