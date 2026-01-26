# GitHub Copilot SDK 官方管道

**作者:** [Fu-Jie](https://github.com/Fu-Jie/awesome-openwebui) | **版本:** 0.1.1 | **项目:** [Awesome OpenWebUI](https://github.com/Fu-Jie/awesome-openwebui) | **许可证:** MIT

这是一个用于 [OpenWebUI](https://github.com/open-webui/open-webui) 的高级 Pipe 函数，允许你直接在 OpenWebUI 中使用 GitHub Copilot 模型（如 `gpt-5`, `gpt-5-mini`, `claude-sonnet-4.5`）。它基于官方 [GitHub Copilot SDK for Python](https://github.com/github/copilot-sdk) 构建，提供了原生级的集成体验。

## 🚀 最新特性 (v0.1.1)

* **♾️ 无限会话 (Infinite Sessions)**：支持长对话的自动上下文压缩，告别上下文超限错误！
* **🧠 思考过程展示**：实时显示模型的推理/思考过程（需模型支持）。
* **📂 工作目录控制**：支持设置受限工作目录，确保文件操作安全。
* **🔍 模型过滤**：支持通过关键词排除特定模型（如 `codex`, `haiku`）。
* **💾 会话持久化**: 改进的会话恢复逻辑，直接关联 OpenWebUI 聊天 ID，连接更稳定。

## ✨ 核心特性

* **🚀 官方 SDK 集成**：基于官方 SDK，稳定可靠。
* **💬 多轮对话支持**：自动拼接历史上下文，Copilot 能理解你的前文。
* **🌊 流式输出 (Streaming)**：支持打字机效果，响应迅速。
* **🖼️ 多模态支持**：支持上传图片，自动转换为附件发送给 Copilot（需模型支持）。
* **🛠️ 零配置安装**：自动检测并下载 GitHub Copilot CLI，开箱即用。
* **🔑 安全认证**：支持 Fine-grained Personal Access Tokens，权限最小化。
* **🐛 调试模式**：内置详细的日志输出，方便排查连接问题。
* **⚠️ 仅支持单节点**：由于会话状态存储在本地，本插件目前仅支持 OpenWebUI 单节点部署，或开启了会话粘性 (Sticky Session) 的多节点集群。

## 📦 安装与使用

### 1. 导入函数

1. 打开 OpenWebUI。
2. 进入 **Workspace** -> **Functions**。
3. 点击 **+** (创建函数)。
4. 将 `github_copilot_sdk_cn.py` 的内容完整粘贴进去。
5. 保存。

### 2. 配置 Valves (设置)

在函数列表中找到 "GitHub Copilot"，点击 **⚙️ (Valves)** 图标进行配置：

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| **GH_TOKEN** | **(必填)** 你的 GitHub Token。 | - |
| **MODEL_ID** | 使用的模型名称。 | `gpt-5-mini` |
| **CLI_PATH** | Copilot CLI 的路径。如果未找到会自动下载。 | `/usr/local/bin/copilot` |
| **DEBUG** | 是否开启调试日志（输出到对话框）。 | `True` |
| **SHOW_THINKING** | 是否显示模型推理/思考过程。 | `True` |
| **EXCLUDE_KEYWORDS** | 排除包含这些关键词的模型 (逗号分隔)。 | - |
| **WORKSPACE_DIR** | 文件操作的受限工作目录。 | - |
| **INFINITE_SESSION** | 启用无限会话 (自动上下文压缩)。 | `True` |
| **COMPACTION_THRESHOLD** | 后台压缩阈值 (0.0-1.0)。 | `0.8` |
| **BUFFER_THRESHOLD** | 缓冲耗尽阈值 (0.0-1.0)。 | `0.95` |
| **TIMEOUT** | 流式数据块超时时间 (秒)。 | `300` |

### 3. 获取 GH_TOKEN

为了安全起见，推荐使用 **Fine-grained Personal Access Token**：

1. 访问 [GitHub Token Settings](https://github.com/settings/tokens?type=beta)。
2. 点击 **Generate new token**。
3. **Repository access**: 选择 **Public repositories** (必须选择此项才能看到 Copilot 权限)。
4. **Permissions**:
    * 点击 **Account permissions**。
    * 找到 **Copilot Requests** (默认即为 **Read-only**，无需手动修改)。
5. 生成并复制 Token。

## 📋 依赖说明

该 Pipe 会自动尝试安装以下依赖（如果环境中缺失）：

* `github-copilot-sdk` (Python 包)
* `github-copilot-cli` (二进制文件，通过官方脚本安装)

## ⚠️ 常见问题

* **一直显示 "Waiting..."**：
  * 检查 `GH_TOKEN` 是否正确且拥有 `Copilot Requests` 权限。
* **图片无法识别**：
  * 确保 `MODEL_ID` 是支持多模态的模型。
* **CLI 安装失败**：
  * 确保 OpenWebUI 容器有外网访问权限。
  * 你可以手动下载 CLI 并挂载到容器中，然后在 Valves 中指定 `CLI_PATH`。
