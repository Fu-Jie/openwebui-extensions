# 📝 Smart Infographic User Prompt (English)

The following is a preset user prompt template. You can save it as an OpenWebUI **Prompt** template for quick access.

**Title**: Generate Infographic
**Command**: `/infographic-en`
**Content**:

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

## 💡 Usage Tips

1.  **Create Prompt**: Go to OpenWebUI **Workspace** -> **Prompts** -> **Create Prompt**.
2.  **Variables**: `{{content}}` is a placeholder. When using it, you can input text directly or let the model auto-fill based on context.
3.  **Invocation**: Type `/` in the chat input box to see your command (e.g., `/infographic-en`), select it, and enter the text you want to convert.
