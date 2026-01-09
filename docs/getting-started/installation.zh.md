# 安装指南

OpenWebUI Extras 提供的资源可以轻松集成到您的 OpenWebUI 实例中。对于大多数用户来说，不需要复杂的环境设置。

## 前置条件

*   运行中的 [OpenWebUI](https://github.com/open-webui/open-webui) 实例。

## 安装插件

您主要有两种方式安装插件：通过 OpenWebUI 社区（推荐）或手动安装。

### 方法 1: OpenWebUI 社区 (推荐)

这是保持插件更新的最简单方法。

1.  访问我在 OpenWebUI 社区的主页: [Fu-Jie's Profile](https://openwebui.com/u/Fu-Jie)。
2.  浏览可用插件并选择您想要安装的。
3.  点击 **Get** 按钮。
4.  按照提示将其直接导入您的本地 OpenWebUI 实例。

### 方法 2: 手动安装

如果您更喜欢下载源代码或特定版本：

1.  导航到本仓库的 `plugins/` 目录或浏览 [插件目录](../plugins/index.md)。
2.  下载您需要的插件的 Python 文件 (`.py`)。
3.  打开您的 OpenWebUI 实例。
4.  转到 **管理面板 (Admin Panel)** -> **设置 (Settings)** -> **插件 (Plugins)**。
5.  点击上传按钮（通常是 `+` 或导入图标）并选择您下载的 `.py` 文件。
6.  上传后，切换开关以启用插件。

## 使用提示词

1.  导航到 `prompts/` 目录或浏览 [提示词库](../prompts/library.md)。
2.  选择适合您任务的提示词文件 (`.md`)。
3.  复制提示词内容。
4.  在 OpenWebUI 聊天界面中，点击 **提示词 (Prompt)** 按钮（通常在输入框附近）。
5.  粘贴内容并将其保存为新提示词，或立即使用。

## 故障排除

如果在安装过程中遇到问题：

*   **插件无法加载**：检查 OpenWebUI 日志是否有语法错误或缺少依赖项。某些插件可能需要在 OpenWebUI 环境中安装特定的 Python 包。
*   **提示词不起作用**：确保您复制了完整的提示词内容。

有关更详细的故障排除，请参阅 [常见问题 (FAQ)](faq.md)。
