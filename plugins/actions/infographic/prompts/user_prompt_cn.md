# 📝 智能信息图用户提示词 (User Prompt - 中文版)

以下是预设的用户提示词模板，你可以将其保存为 OpenWebUI 的 **Prompt (提示词)** 模板，方便快速调用。

**Title (标题):** 生成信息图
**Command (命令):** `/infographic-cn`
**Content (内容):**

```markdown

**任务说明**

请分析以上提供的内容，将其核心逻辑与数据提炼出来，并按照指定的【模板】和【风格】生成规范的 infographic 语法代码块。

**选择模板：**
{{template_name | select:options=["网格列表 (list-grid)", "垂直列表 (list-vertical)", "垂直树图 (tree-vertical)", "水平树图 (tree-horizontal)", "思维导图 (mindmap)", "路线图 (sequence-roadmap)", "蛇形流程 (sequence-zigzag)", "循环关系 (relation-circle)", "二元对比 (compare-binary)", "SWOT分析 (compare-swot)", "四象限图 (quadrant-quarter)", "统计卡片 (statistic-card)", "柱状图 (chart-bar)", "列状图 (chart-column)", "折线图 (chart-line)", "饼图 (chart-pie)"]:default="网格列表 (list-grid)"}}

**视觉风格：**
{{style_mode | select:options=["默认 (default)", "手绘 (rough)"]:default="默认 (default)"}}

**配色主题：**
{{theme_type | select:options=["默认 (default)", "深色 (dark)", "科技 (tech)", "暖色 (warm)", "冷色 (cool)"]:default="默认 (default)"}}

**输出要求**

请直接输出以 \`\`\`infographic 开头的代码块。
1.  **模板**: 使用 {{template_name}} 中括号内的英文代码。
2.  **风格**: 在 theme 块中设置 `stylize` 为 {{style_mode}} 中括号内的英文代码（如果是 default 则不设置）。
3.  **主题**: 在 theme 块中应用 {{theme_type}} 中括号内的英文代码对应的配色。
4.  **纯净输出**: 不要输出任何额外的解释说明。
```

## 💡 使用技巧

1.  **创建提示词**: 在 OpenWebUI 中进入 **Workspace** -> **Prompts** -> **Create Prompt**。
2.  **设置变量**: 上述模板中的 `{{content}}` 是变量占位符。在使用时，你可以直接输入文本，或者让模型基于上下文自动填充。
3.  **调用方式**: 在聊天输入框输入 `/` 即可看到你创建的命令（如 `/infographic-cn`），选中后输入你想转换的文本即可。
