# GitHub Copilot SDK 文件过滤器

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 0.1.2 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个专门为 [GitHub Copilot SDK Pipe](https://openwebui.com/posts/github_copilot_official_sdk_pipe_ce96f7b4) 设计的**伴侣过滤器插件**。

它的核心使命是：**保护用户上传的文件不被 OpenWebUI 核心系统“抢先处理”，确保 Copilot Agent 能够接收到原始文件并进行自主分析。**

## 🎯 为什么需要它？

在 OpenWebUI 的默认流程中，当你上传一个文件（如 PDF、Excel、Python 脚本）时，OpenWebUI 会自动启动 **RAG（检索增强生成）** 流程：解析文件、向量化、提取文本并注入到提示词中。

虽然这对普通模型很有用，但对于 **Copilot SDK Agent** 来说，这往往是干扰：

1. **Agent 需要原始文件**：Agent 可能需要运行 Python 代码读取 Excel，或者分析完整的代码结构，而不是被切碎的文本片段。
2. **上下文污染**：RAG 注入的大量文本会消耗 Token，且容易让 Agent 混淆“文件在哪里”。
3. **控制权与性能**：绕过提取步骤可以加快响应速度，并赋予 Agent 处理数据的完全自主权。

**本插件就是为了解决这个问题而生的“保镖”。**

## 🚀 功能原理

当你在 OpenWebUI 中选择了一个 Copilot 模型（名称包含 `copilot_sdk`）并发送文件时：

1. **拦截 (Intercept)**：本插件会以极高的优先级（Priority 5）运行，先于 RAG 和其他过滤器。
2. **搬运 (Relocate)**：它检测到模型是 Copilot，便将请求中的 `files`（文件列表）移动到一个安全的自定义字段 `copilot_files` 中。
3. **隐身 (Hide)**：它清空原始的 `files` 字段。
4. **放行 (Pass)**：OpenWebUI 核心看到 `files` 为空，便**不会触发 RAG**。
5. **交付 (Deliver)**：后续的 Copilot SDK Pipe 插件会检查 `copilot_files`，从中获取文件信息，并自动将其复制到 Agent 的独立工作区中。

## 📦 安装与配置

### 1. 安装

在 OpenWebUI 的 **Functions** 页面导入此插件。

### 2. 启用

确保在全局或对话设置中启用了此 Filter。

### 3. 配置 (Valves)

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| **priority** | 过滤器的执行优先级。**必须小于 OpenWebUI RAG 的优先级**。 | `5` |
| **target_model_keyword** | 用户识别 Copilot 模型的关键词。只有包含此关键词的模型才会触发。 | `copilot_sdk` |

## ⚠️ 注意事项

* **必须配合 Copilot SDK Pipe 使用**：如果你没有安装主 Pipe 插件，本插件将导致上传的文件“凭空消失”。
* **Gemini Filter 兼容性**：已完美兼容 Gemini 多模态过滤器。只要优先级设置正确，它们可以共存互不干扰。
