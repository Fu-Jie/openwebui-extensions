# 📝 智能信息图用户提示词 (User Prompts)

以下是预设的用户提示词模板，你可以将其保存为 OpenWebUI 的 **Prompt (提示词)** 模板，方便快速调用。

---

## 🇨🇳 中文版本 (Chinese)

**Title (标题):** 生成信息图
**Command (命令):** `/infographic-cn`
**Content (内容):**

```markdown
请分析以下文本内容，将其核心信息转换为 AntV Infographic 语法格式。

**文本内容:**
{{content}}

**要求:**
1.  根据文本特点选择最合适的信息图模板（如列表、流程图、对比图、统计图等）。
2.  输出规范的 `infographic` 语法代码块。
3.  如果使用 `list-grid` 格式，请确保每个卡片的描述文字简练（约30字以内）。
4.  保持两空格缩进，不要使用冒号作为键值对分隔符。
```

---

## 🇺🇸 英文版本 (English)

**Title (标题):** Generate Infographic
**Command (命令):** `/infographic-en`
**Content (内容):**

```markdown
Please analyze the following text content and convert its core information into AntV Infographic syntax format.

**Text Content:**
{{content}}

**Requirements:**
1.  Choose the most appropriate infographic template based on the content (e.g., list, flowchart, comparison, chart, etc.).
2.  Output a valid `infographic` syntax code block.
3.  If using `list-grid` format, ensure card descriptions are concise (around 60 characters).
4.  Use two-space indentation and do NOT use colons for key-value pairs.
```

---

## 💡 使用技巧

1.  **创建提示词**: 在 OpenWebUI 中进入 **Workspace** -> **Prompts** -> **Create Prompt**。
2.  **设置变量**: 上述模板中的 `{{content}}` 是变量占位符。在使用时，你可以直接输入文本，或者让模型基于上下文自动填充。
3.  **调用方式**: 在聊天输入框输入 `/` 即可看到你创建的命令（如 `/infographic-cn`），选中后输入你想转换的文本即可。
