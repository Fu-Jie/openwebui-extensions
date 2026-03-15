# iFlow 官方 SDK Pipe 插件

此插件将 [iFlow SDK](https://platform.iflow.cn/cli/sdk/sdk-python) 集成到 OpenWebUI 中。

## 功能特性

- **标准 iFlow 集成**：通过 WebSocket (ACP) 连接到 iFlow CLI 进程。
- **自动进程管理**：如果 iFlow 进程未运行，将自动启动。
- **流式输出支持**：支持从 iFlow 到聊天界面的实时流式输出。
- **实时状态更新**：在 UI 中实时显示助手状态（思考中、工具调用等）。
- **工具调用可视化**：实时反馈 iFlow 调用及完成工具的过程。

## 配置项 (Valves)

- `IFLOW_PORT`：iFlow CLI 进程端口（默认：`8090`）。
- `IFLOW_URL`：WebSocket 地址（默认：`ws://localhost:8090/acp`）。
- `AUTO_START`：是否自动启动进程（默认：`True`）。
- `TIMEOUT`：请求超时时间（秒）。
- `LOG_LEVEL`：SDK 日志级别（DEBUG, INFO 等）。

## 安装说明

此插件同时依赖 **iFlow CLI** 二进制文件和 **iflow-cli-sdk** Python 包。

### 1. 安装 iFlow CLI (系统层级)

在系统中执行以下命令（适用于 Linux/macOS）：

```bash
bash -c "$(curl -fsSL https://gitee.com/iflow-ai/iflow-cli/raw/main/install.sh)"
```

### 2. 安装 Python SDK (OpenWebUI 环境)

```bash
pip install iflow-cli-sdk
```
