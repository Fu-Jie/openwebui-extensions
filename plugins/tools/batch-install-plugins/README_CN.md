# Batch Install Plugins from GitHub

| 作者：[Fu-Jie](https://github.com/Fu-Jie) · v1.1.0 | [⭐ 点个 Star 支持项目](https://github.com/Fu-Jie/openwebui-extensions) |
| :--- | ---: |

| ![followers](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_followers.json&label=%F0%9F%91%A5&style=flat) | ![points](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_points.json&label=%E2%AD%90&style=flat) | ![top](https://img.shields.io/badge/%F0%9F%8F%86-Top%20%3C1%25-10b981?style=flat) | ![contributions](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_contributions.json&label=%F0%9F%93%A6&style=flat) | ![downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_downloads.json&label=%E2%AC%87%EF%B8%8F&style=flat) | ![saves](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_saves.json&label=%F0%9F%92%BE&style=flat) | ![views](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2FFu-Jie%2Fdb3d95687075a880af6f1fba76d679c6%2Fraw%2Fbadge_views.json&label=%F0%9F%91%81%EF%B8%8F&style=flat) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |

一键将 GitHub 仓库中的插件批量安装到你的 OpenWebUI 实例。

## 使用 Batch Install Plugins 安装

当你已经安装过一次 [Batch Install Plugins from GitHub](https://openwebui.com/posts/batch_install_plugins_install_popular_plugins_in_s_c9fd6e80) 后，也可以用同一句来重新安装或更新它自己：

```text
从 Fu-Jie/openwebui-extensions 安装插件
```

当选择弹窗打开后，搜索当前插件，勾选后继续安装即可。

> [!IMPORTANT]
> 如果你已经安装了 OpenWebUI 官方社区里的同名版本，请先删除旧版本，否则重新安装时可能报错。删除后，Batch Install Plugins 后续就可以继续负责更新这个插件。

> [!TIP]
> **💡 想要批量安装/管理 Workspace 技能 (Skills)？**
> 本插件专注安装全局函数型插件（Pipe/Filter/Tool/Action）。如果你需要管理 AI 助手的专属技能，请使用同系列的 [OpenWebUI Skills Manager](https://openwebui.com/posts/openwebui_skills_manager_tool_b4bce8e4) 工具，它具备完整的增删改查、批量发现及可视化浮层点选能力。

## 主要功能

- 一键安装：单个命令安装所有插件
- 自动更新：自动更新之前安装过的插件
- 公开 GitHub 支持：支持从一个或多个公开 GitHub 仓库安装插件
- 多类型支持：支持 Pipe、Action、Filter 和 Tool 插件
- 多仓库选择器：一次请求可合并多个仓库，并在同一个分组对话框中查看
- 交互式选择对话框：先按仓库和类型筛选、按关键词搜索并查看描述信息，再勾选要安装的插件，只安装所选子集
- 国际化：支持 11 种语言

## 流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  从 GitHub 多仓库发现插件            │
│  (获取文件树 + 解析 .py 文件)        │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  按类型和关键词过滤                  │
│  (tool/filter/pipe/action)         │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  显示选择对话框                      │
│  (仓库分组 + 筛选 + 搜索)            │
└─────────────────────────────────────┘
    │
    ├── [取消] → 结束
    │
    ▼
┌─────────────────────────────────────┐
│  安装到 OpenWebUI                   │
│  (更新或创建每个插件)                │
└─────────────────────────────────────┘
    │
    ▼
   完成
```

## 使用方法

1. 打开 OpenWebUI，进入 **Workspace > Tools**
2. 从市场安装 **Batch Install Plugins from GitHub**
3. 为你的模型/对话启用此工具
4. 让模型调用工具来安装插件

## 交互式安装工作流

`repo` 参数现在支持多个 `owner/repo`，可用逗号、分号或换行分隔。

在插件发现和过滤完成后，OpenWebUI 会通过 `execute` 事件打开浏览器选择对话框。对话框会合并所有目标仓库的结果，按仓库分组展示，并支持仓库标签、类型筛选、关键词搜索和描述查看，再开始调用安装 API。

如果一次用户请求里提到了多个仓库，尽量保持在同一次请求里，让模型把它们合并到一次工具调用中。

## 快速开始：安装热门插件集

复制下面这条提示词，粘贴到你的对话框中：

```
从 Fu-Jie/openwebui-extensions、iChristGit/OpenWebui-Tools、Haervwe/open-webui-tools、Classic298/open-webui-plugins、suurt8ll/open_webui_functions、rbb-dev/Open-WebUI-OpenRouter-pipe 安装所有插件
```

弹窗出现后，直接用里面的仓库标签、类型筛选和关键词搜索来缩小范围再安装。已安装的插件会自动更新。

需要时，你也可以把这串仓库替换成你自己的插件仓库组合。

## 默认仓库

未指定仓库时，工具会使用 `Fu-Jie/openwebui-extensions`（我的个人合集）。

## 插件检测规则

### Fu-Jie/openwebui-extensions（严格模式）

对于默认仓库，工具会采用更严格的筛选规则：
1. 包含 `class Tools:`、`class Filter:`、`class Pipe:` 或 `class Action:` 的 `.py` 文件
2. Docstring 中包含 `title:`、`description:` 和 **`openwebui_id:`** 元数据
3. 文件名不能以 `_cn` 结尾

### 其他公开 GitHub 仓库

其他仓库的插件必须满足：
1. 包含 `class Tools:`、`class Filter:`、`class Pipe:` 或 `class Action:` 的 `.py` 文件
2. Docstring 中包含 `title:` 和 `description:` 字段

## 配置（Valves）

| 参数 | 默认值 | 描述 |
| --- | --- | --- |
| `SKIP_KEYWORDS` | `test,verify,example,template,mock` | 逗号分隔的跳过关键词 |
| `TIMEOUT` | `20` | 请求超时时间（秒）|

## 选择对话框超时时间

插件选择对话框的默认超时时间为 **2 分钟（120 秒）**，为用户提供充足的时间来：
- 阅读和查看插件列表
- 勾选或取消勾选想安装的插件
- 处理网络延迟

## 支持

⭐ 如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。
