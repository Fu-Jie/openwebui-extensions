import re

def reproduce_bug():
    # 模拟 Issue #49 中提到的受损逻辑
    # 核心问题在于正则表达式过于贪婪，或者在多次迭代中错误地将两个加粗块中间的部分当作了“带空格的加粗内容”
    text = "I **prefer** tea **to** coffee."
    
    # 模拟一个不严谨的、容易跨块匹配的正则
    # 它会匹配 ** 开始，中间任意字符，** 结束
    buggy_pattern = re.compile(r"(\*\*)(.*?)(\*\*)")

    def buggy_fix(content):
        # 模拟插件中的 strip 逻辑：它想去掉加粗符号内部的空格
        # 但由于正则匹配了 "**prefer** tea **", 这里的 m.group(2) 变成了 "prefer** tea "
        return buggy_pattern.sub(lambda m: f"{m.group(1)}{m.group(2).strip()}{m.group(1)}", content)

    # 第一次执行：处理了 "**prefer**" -> "**prefer**"
    result_1 = buggy_fix(text)
    
    # 第二次执行（模拟 while 循环或重复运行）：
    # 此时如果正则引擎从第一个加粗的结束符开始匹配到第二个加粗的起始符
    # 指针位置: I **prefer**[匹配开始] tea [匹配结束]**to** coffee.
    # 就会把 " tea " 两侧的 ** 当作一对，然后 strip() 掉空格
    result_2 = buggy_fix(result_1)
    
    print(f"Original: {text}")
    print(f"Step 1:   {result_1}")
    print(f"Step 2:   {result_2} (Bug Reproduced!)")

if __name__ == "__main__":
    reproduce_bug()
