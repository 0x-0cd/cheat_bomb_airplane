from entities.solution import Solution
import strategies.strategy_3


def main():
    sol = Solution()
    strategies.strategy_3.solve(sol)

    # print("【策略3】")
    # strategies.strategy_3.bench_mark(100)


if __name__ == "__main__":
    main()
