# Markdown Normalizer v1.2.8 测试用例集

您可以将以下内容逐个复制到 OpenWebUI 的聊天框中，以验证插件的各项修复功能。

---

## 用例 1：验证 SQL 代码块换行修复 (需要手动开启配置)

**测试目的**：验证 `enable_escape_fix_in_code_blocks` 开关是否生效。
**前提条件**：请先在插件 Valves 设置中将 `enable_escape_fix_in_code_blocks` 设置为 **开启 (True)**。

**复制以下内容：**
```text
请帮我美化这段 SQL 的排版，使其恢复正常换行：

```sql
SELECT * \n FROM users \n WHERE status = 'active' \n AND created_at > '2024-01-01' \n ORDER BY id DESC;
```
```

**预期效果**：SQL 代码块内的 `\n` 消失，变为整齐的多行 SQL 语句。

---

## 用例 2：验证上下文感知保护 (防止误伤技术内容)

**测试目的**：验证插件是否能准确识别“纯文本”和“代码区域”，只修复该修复的地方。
**配置要求**：默认配置即可。

**复制以下内容：**
```text
这是一个综合测试用例。

1. 普通文本修复测试：
这是第一行\\n这是第二行（你应该看到这里发生了换行）。

2. 行内代码保护测试（不应被修改）：
- 正则表达式：`[\n\r\t]`
- Windows 路径：`C:\Windows\System32\drivers\etc\hosts`
- 转义测试：`\\n` 应该保持字面量。

3. LaTeX 命令保护测试：
这里的数学公式 $\times \theta \nu \sum$ 应该渲染正常，反斜杠不应被修掉。

4. 现代 LaTeX 定界符转换：
\[ E = mc^2 \]
（上面这行应该被自动转换为 $$ 包围的块级公式）
```

**预期效果**：
- 第一部分的 `\\n` 成功换行。
- 第二部分反引号 `` ` `` 里的内容原封不动。
- 第三部分的希腊字母公式渲染正常。
- 第四部分的 `\[` 变成了 `$$` 且能正常显示公式。

---

## 用例 3：验证思维链与详情标签规范化

**测试目的**：验证对 `<thought>` 和 `<details>` 标签的排版优化。

**复制以下内容：**
```text
<thinking>
这是一个正在思考的思维链。
</thinking>
<details>
<summary>点击查看详情</summary>
这里的排版通常容易出错。
</details>
紧接着详情标签的文字（应该和上面有空行隔开）。
```

**预期效果**：
- `<thinking>` 标签被统一为 `<thought>`。
- `</details>` 标签下方自动注入了空行，防止与正文粘连导致渲染失效。

---

## 用例 4：极端压力与回滚测试 (稳定性验证)

**测试目的**：模拟复杂嵌套环境，验证 100% 回滚机制。

**复制以下内容：**
```text
尝试混合所有复杂元素：
- 列表项 1
- 列表项 2 with `inline \\n code`
- $ \text{Math } \alpha $
```sql
-- SQL with nested issue
SELECT 'literal \n string' FROM `table`;
```
<thought>End of test</thought>
```

**预期效果**：
- 无论内部处理逻辑多么复杂，插件都应保证输出稳定的结果。
- 如果模拟任何内部崩溃（技术人员可用），消息会回滚至此原始文本，不会导致页面白屏。
