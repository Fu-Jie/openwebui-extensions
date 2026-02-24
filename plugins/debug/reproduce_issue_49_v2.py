import re

def reproduce_bug_v2():
    # 模拟更接近旧版实际代码的情况
    # 旧版代码中循环多次处理，且正则可能在处理嵌套或连续块时出现偏移
    text = "I **prefer** tea **to** coffee."
    
    # 这是一个贪婪且不具备前瞻断言的正则
    buggy_pattern = re.compile(r"(\*\*)( +)(.*?)( +)(\*\*)")

    # 模拟那种“只要看到 ** 且中间有空格就想修”的逻辑
    # 如果文本是 "I **prefer** tea **to**"
    # 这里的空格出现在 "prefer**" 和 "**to" 之间
    content = "I **prefer**  tea  **to** coffee."
    
    # 错误的匹配尝试：将第一个块的结尾和第二个块的开头误认为是一对
    # I **prefer**  tea  **to**
    #          ^^      ^^ 
    #          A       B
    # 正则误以为 A 是开始，B 是结束
    
    bug_result = re.sub(r"\*\*( +)(.*?)( +)\*\*", r"**\2**", content)
    
    print(f"Input:  {content}")
    print(f"Output: {bug_result}")

if __name__ == "__main__":
    reproduce_bug_v2()
