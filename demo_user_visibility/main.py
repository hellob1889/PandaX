"""Demo main script - MODIFIED BY AGENT."""

def add(a, b):
    # Agent 修改: 加减切换演示
    return a - b  # BUG: 应该是 a + b

if __name__ == "__main__":
    print(add(1, 2))  # 现在输出 -1
