# Batch Install Plugins from GitHub

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 1.1.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

一键将 GitHub 仓库中的插件批量安装到你的 OpenWebUI 实例。

## 主要功能

- 一键安装：单个命令安装所有插件
- 自动更新：自动更新之前安装过的插件
- 公开 GitHub 支持：支持从任何公开 GitHub 仓库安装插件
- 多类型支持：支持 Pipe、Action、Filter 和 Tool 插件
- 交互式选择对话框：先查看过滤后的列表，再勾选要安装的插件，只安装所选子集
- 国际化：支持 11 种语言

## 流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  从 GitHub 发现插件                  │
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
│  (复选列表 + 排除提示)              │
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

每次请求处理一个仓库。如需混合多个来源，请在上一次安装完成后再发起下一次请求。

在插件发现和过滤完成后，OpenWebUI 会通过 `execute` 事件打开浏览器选择对话框，你可以先勾选真正想安装的插件，再开始调用安装 API。

## 快速开始：安装热门插件集

复制以下任一提示词，粘贴到你的对话框中：

```
# 安装我的默认集合
安装所有插件

# 添加热门社区工具
从 iChristGit/OpenWebui-Tools 安装所有插件

# 添加实用工具扩展
从 Haervwe/open-webui-tools 安装所有插件

# 添加混合社区实现
从 Classic298/open-webui-plugins 安装所有插件

# 添加基于函数的插件
从 suurt8ll/open_webui_functions 安装所有插件

# 添加 OpenRouter 管道集成
从 rbb-dev/Open-WebUI-OpenRouter-pipe 安装所有插件
```

每一行是一个独立的请求。已安装的插件会自动更新。

## 使用示例

更多高级用法：

```
# 按插件类型过滤
"从 iChristGit/OpenWebui-Tools 仅安装 tool 插件"
"从 Classic298/open-webui-plugins 仅安装 action 插件"

# 排除特定插件
"从 Haervwe/open-webui-tools 安装所有插件, exclude_keywords=test,deprecated"

# 从你自己的仓库安装
"从 your-username/my-plugin-collection 安装所有插件"
```

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
