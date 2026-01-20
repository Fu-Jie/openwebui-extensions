# 文件夹记忆 (Folder Memory)

[English](./README.md) | 中文

**文件夹记忆 (Folder Memory)** (原名 Folder Rule Collector) 是一个 OpenWebUI 的智能上下文过滤器插件。它能自动从文件夹内的对话中提取一致性的“项目规则”，并将其回写到文件夹的系统提示词中。

这确保了该文件夹内的所有未来对话都能共享相同的进化上下文和规则，无需手动更新。

## ✨ 功能特性

- **自动提取**：每隔 N 条消息分析一次聊天记录，提取项目规则。
- **无损注入**：仅更新系统提示词中的特定“项目规则”块，保留其他指令。
- **异步处理**：在后台运行，不阻塞用户的聊天体验。
- **ORM 集成**：直接使用 OpenWebUI 的内部模型更新文件夹数据，确保可靠性。

## 📦 安装指南

1. 将 `folder_memory.py` (或中文版 `folder_memory_cn.py`) 复制到 OpenWebUI 的 `plugins/filters/` 目录（或通过管理员 UI 上传）。
2. 在 **设置** -> **过滤器** 中启用该插件。
3. （可选）配置触发阈值（默认：每 10 条消息）。

## ⚙️ 配置 (Valves)

| 参数 | 默认值 | 说明 |
| :--- | :--- | :--- |
| `PRIORITY` | `20` | 过滤器操作的优先级。 |
| `MESSAGE_TRIGGER_COUNT` | `10` | 触发规则分析的消息数量阈值。 |
| `MODEL_ID` | `""` | 用于生成规则的模型 ID。若为空，则使用当前对话模型。 |
| `RULES_BLOCK_TITLE` | `## 📂 项目规则` | 显示在注入规则块上方的标题。 |
| `SHOW_DEBUG_LOG` | `False` | 在浏览器控制台显示详细调试日志。 |
| `UPDATE_ROOT_FOLDER` | `False` | 如果启用，将向上查找并更新根文件夹的规则，而不是当前子文件夹。 |

## 🛠️ 工作原理

![Folder Memory Demo](https://raw.githubusercontent.com/Fu-Jie/awesome-openwebui/main/plugins/filters/folder-memory/folder-memory-demo.png)

1. **触发**：当对话达到 `MESSAGE_TRIGGER_COUNT`（例如 10、20 条消息）时。
2. **分析**：插件将最近的对话 + 现有规则发送给 LLM。
3. **综合**：LLM 将新见解与旧规则合并，移除过时的规则。
4. **更新**：新的规则集替换文件夹系统提示词中的 `<!-- OWUI_PROJECT_RULES_START -->` 块。

## ⚠️ 注意事项

- 此插件会修改文件夹的 `system_prompt`。
- 它使用特定标记 `<!-- OWUI_PROJECT_RULES_START -->` 来定位内容。如果您希望插件继续管理该部分，请勿手动删除这些标记。

## 🗺️ 路线图

查看 [ROADMAP.md](./ROADMAP.md) 了解未来计划，包括“项目知识”收集功能。
