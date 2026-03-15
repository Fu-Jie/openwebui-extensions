# Batch Install Plugins from GitHub

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 1.0.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

一键将 GitHub 仓库中的插件批量安装到你的 OpenWebUI 实例。

## 主要功能

- 一键安装：单个命令安装所有插件
- 自动更新：自动更新之前安装过的插件
- 公开 GitHub 支持：支持从任何公开 GitHub 仓库安装插件
- 多类型支持：支持 Pipe、Action、Filter 和 Tool 插件
- 安装确认：安装前显示插件列表，支持选择性安装
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
│  显示确认对话框                      │
│  (插件列表 + 排除提示)              │
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

### 安装序列示例

1. **先从我的合集开始**
   ```
   "安装 Fu-Jie/openwebui-extensions 中的所有插件"
   ```
   查看确认对话框，批准后插件开始安装。

2. **再添加社区合集**
   ```
   "从 iChristGit/OpenWebui-Tools 安装所有插件"
   ```
   从不同仓库添加更多插件。已安装的插件会无缝更新。

3. **按类型继续安装**
   ```
   "从 Haervwe/open-webui-tools 仅安装 pipe 插件"
   ```
   从另一个仓库选择特定类型的插件，或排除某些关键词。

4. **使用你自己的仓库**
   ```
   "从 your-username/your-collection 安装所有插件"
   ```
   支持任何公开的 GitHub 仓库，格式为 `owner/repo`。

## 使用示例

下面每一行都是一次独立请求：

```
# 从默认合集安装
"安装所有插件"

# 在下一次请求中加入其他仓库
"从 iChristGit/OpenWebui-Tools 安装所有插件"

# 从其他仓库只安装工具
"从 Haervwe/open-webui-tools 仅安装 tool 插件"

# 再继续补充另一类插件
"从 Classic298/open-webui-plugins 安装仅 action 插件"

# 过滤不想安装的插件
"从 Haervwe/open-webui-tools 安装所有插件, exclude_keywords=test,deprecated"

# 从你自己的公开仓库安装
"从 your-username/my-plugin-collection 安装所有插件"
```

## 热门公开仓库

该工具支持任何公开 GitHub 仓库，格式为 `owner/repo`。这些都是不错的起点：

- `Fu-Jie/openwebui-extensions` - 我的个人合集，也是默认来源
- `iChristGit/OpenWebui-Tools` - 全面的工具和插件集合
- `Haervwe/open-webui-tools` - 偏工具型的扩展集合
- `Classic298/open-webui-plugins` - 混合型社区插件集合
- `suurt8ll/open_webui_functions` - 基于函数的插件集合
- `rbb-dev/Open-WebUI-OpenRouter-pipe` - OpenRouter pipe 集成

如需混合多个来源，请在上一次安装完成后，换一个 `repo` 再调用一次工具。

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

## 确认超时时间

用户确认对话框的默认超时时间为 **2 分钟（120 秒）**，为用户提供充足的时间来：
- 阅读和查看插件列表
- 做出安装决定
- 处理网络延迟

## 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。
