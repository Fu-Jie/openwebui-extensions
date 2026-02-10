# GitHub Copilot SDK 插件进阶实战教程

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 1.0.0 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui)

本教程旨在指导您如何深度发挥 GitHub Copilot SDK 插件的全部潜力，特别是在自动化文件生成、BYOK 模式自定义以及复杂任务调度方面的进阶用法。

---

## 1. 核心协议：文件交付三步法 (File Delivery Protocol)

这是本插件最强大的功能之一。Agent 不再只是“说话”，它可以在其隔离的工作区内生成真正的物理文件（如 `.xlsx`, `.pdf`, `.csv`），并将其发布给您下载。

### 自动化执行逻辑：
1.  **本地写入 (Write)**：Agent 在其隔离目录（即 Python 执行的当前目录 `.`）下通过代码生成文件。
2.  **显式发布 (Publish)**：Agent 自动调用 `publish_file_from_workspace(filename='report.xlsx')`。
3.  **获取链接 (Link)**：插件会自动处理 S3 或本地存储映射，绕过 RAG 干扰，并返回一个类似 `/api/v1/files/.../content` 的安全链接。

> [!TIP]
> **用户指令技巧**：您可以直接对 Agent 说：“分析刚才的表格并导出一份 Excel 给我”。它会自动触发这一连串动作。

---

## 2. BYOK (自带 Key) 模式进阶

如果您没有 GitHub Copilot 订阅，或者希望使用自己购买的 OpenAI/Anthropic 高阶模型，可以使用 BYOK 模式。

### 如何配置：
1.  **设置 Base URL**：如 `https://api.openai.com/v1`。
2.  **设置 API Key**：在个人设置中填入您的密钥。
3.  **模型实时刷新**：插件具备**配置感知刷新**机制。当您在 Valve 中修改了 API Key 或 Base URL 后，无需重启，只需刷新模型选择器，插件会自动向后端拉取最新的可用模型列表。

---

## 3. 工作区隔离与调试 (Workspace & Debugging)

每个聊天会话都有一个物理上隔离的文件夹，确保不同任务的文件互不干扰。

### 物理路径规则：
- **容器内路径**：`/app/backend/data/copilot_workspace/{user_id}/{chat_id}/`
- **Agent 的视角**：它看到的 `.` 目录即是上述路径。

### 调试秘籍：
1.  **开启 DEBUG Valve**：在配置中将 `DEBUG` 设为 `True`。
2.  **查看控制台**：打开浏览器开发者工具 (F12) -> Console。
3.  **捕获路径**：您会看到类似 `📂 Workspace Resolved: /.../` 的日志，这能帮您确认 Agent 到底把文件写到了哪里。

---

## 4. 绕过 RAG 的深度分析

传统的 OpenWebUI 文件上传会触发向量化（RAG），这对于大批量数据分析往往不够精确。

**本插件的优势**：
- 配合 [Files Filter](https://openwebui.com/posts/403a62ee-a596-45e7-be65-fab9cc249dd6) 插件使用时，Agent 可以**直接读取**原始文件的每一个字节。
- 它能像在本地运行脚本一样分析 CSV 的每一行，而不会因为切片检索（Retrieval）导致信息丢失。

---

## 5. 常见交互指令示例

- **数据转换**：“把这个 JSON 内容转换成格式精美的 Word 文档并提供下载链接。”
- **代码审查**：“读取工作区内的所有 `.py` 文件，找出潜在的 Bug，并把修改建议发布为 Markdown 报告。”
- **图表生成**：“根据刚才的财务数据生成一份 Excel 报表，并用 Python 画一个趋势图给我。”

---

## 🚀 实战示例：全自动财务分析报告

### 场景描述
用户上传了一个名为 `sales_data.csv` 的原始销售清单，要求 AI 进行汇总统计，并生成一份带样式的 Excel 报表。

### 1. 用户的指令
> “请分析当前目录下的 `sales_data.csv`，按产品类别统计总销售额，并导出一份名为 `category_summary.xlsx` 的 Excel 给我就好。”

### 2. Agent 的自动化执行过程
Agent 会在后台连续执行以下动作：

*   **步骤 1: 编写并运行 Python 脚本**
    ```python
    import pandas as pd
    # 直接在隔离工作区读取原始文件（绕过 RAG，保证数据 100% 准确）
    df = pd.read_csv('sales_data.csv')
    summary = df.groupby('Category')['Revenue'].sum().reset_index()
    # 保存结果到当前目录
    summary.to_excel('category_summary.xlsx', index=False)
    ```
*   **步骤 2: 调用发布工具**
    Agent 自动执行工具调用：`publish_file_from_workspace(filename="category_summary.xlsx")`
*   **步骤 3: 交付链接**
    工具返回 `download_url`，Agent 最终回复用户。

### 3. 最终交付效果
Agent 会向用户展示：
> “分析完成！我已经为您统计了产品类别的销售额。您可以点击下方链接下载报表：
> 
> [📊 点击下载：分类销售统计报表.xlsx](/api/v1/files/uuid-hash/content)”

#### 实际运行截图示例
![GitHub Copilot SDK 测试结果](2026-02-10_165530.png)

---

## ⭐ 持续改进

如果您在使用过程中发现任何问题，或有新的功能建议，欢迎到 [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) 提交 Issue 或参与讨论。
