import re

def verify_fix_v126():
    # 1. 准备触发 Bug 的测试文本
    test_cases = [
        "I **prefer** tea **to** coffee.",                  # 标准 Issue #49 案例
        "The **quick** brown **fox** jumps **over**.",       # 多个加粗块
        "** text ** and ** more **",                       # 需要修复的内部空格
        "Calculations: 2 * 3 * 4 = 24",                     # 不应被识别为强调的数学公式
    ]

    # 2. 使用 v1.2.6 中的核心正则表达式 (移除了可能引起解析错误的中文注释)
    # 模式: (?<!\*|_)(\*{1,3}|_{1,3})(?P<inner>(?:(?!\1)[^\n])*?)(\1)(?!\*|_)
    pattern_str = r"(?<!\*|_)(\*{1,3}|_{1,3})(?P<inner>(?:(?!\1)[^\n])*?)(\1)(?!\*|_)"
    FIX_REGEX = re.compile(pattern_str)

    def fixed_normalizer(content):
        def replacer(match):
            symbol = match.group(1)
            inner = match.group("inner")
            
            stripped_inner = inner.strip()
            
            # 只有当确实有空格需要修，且内部不是空的才修复
            if stripped_inner != inner and stripped_inner:
                return f"{symbol}{stripped_inner}{symbol}"
            return match.group(0)

        # 模拟插件循环处理
        for _ in range(2):
            content = FIX_REGEX.sub(replacer, content)
        return content

    print("--- v1.2.6 Fix Verification ---")
    for text in test_cases:
        result = fixed_normalizer(text)
        print(f"Input:  {text}")
        print(f"Output: {result}")
        print("-" * 30)

if __name__ == "__main__":
    verify_fix_v126()
