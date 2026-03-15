# Batch Install Plugins from GitHub - 从 GitHub 批量安装插件

**作者:** [Fu-Jie](https://github.com/Fu-Jie) | **版本:** 1.0.0 | **项目:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) | **许可:** MIT

---

一键从 GitHub 仓库批量安装插件到你的 OpenWebUI 实例。

## ✨ 主要特性

- **一键安装**: 一条命令安装所有插件
- **自动更新**: 自动更新之前已安装的插件
- **GitHub 支持**: 支持从任何 GitHub 仓库安装插件
- **多类型支持**: 支持 Pipe、Action、Filter 和 Tool 插件
- **确认机制**: 安装前显示插件列表，允许选择性安装
- **国际化**: 支持 11 种语言

## 工作流

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│  从 GitHub 发现插件                  │
│  (获取文件树 + 解析 .py)            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  按类型和关键词过滤                  │
│  (tool/filter/pipe/action)          │
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
│  安装到 OpenWebUI                    │
│  (更新或创建每个插件)               │
└─────────────────────────────────────┘
    │
    ▼
   完成
```

## 🚀 使用方法

1. 打开 OpenWebUI，进入 **工作区 > 工具**
2. 从官方市场安装 **Batch Install Plugins from GitHub**
3. 为你的模型/聊天启用此工具
4. 让模型安装插件

## 使用示例

```
"安装所有插件"
"从 github.com/username/repo 安装所有插件"
"仅安装 pipe 插件"
"安装 action 和 filter 插件"
"安装所有插件，exclude_keywords=copilot"
```

## 热门插件仓库

这些是包含大量插件的热门仓库，你可以从中安装插件：

### 社区合集

```
# 从 iChristGit 的集合安装所有插件
"从 iChristGit/OpenWebui-Tools 安装所有插件"

# 从 Haervwe 的工具集合只安装工具
"从 Haervwe/open-webui-tools 安装所有插件"

# 从 Classic298 的仓库安装所有插件
"从 Classic298/open-webui-plugins 安装所有插件"

# 从 suurt8ll 的集合安装所有函数
"从 suurt8ll/open_webui_functions 安装所有插件"

# 仅安装特定类型的插件（比如只安装工具）
"从 iChristGit/OpenWebui-Tools 仅安装 tool 插件"

# 安装时排除特定关键词
"从 Haervwe/open-webui-tools 安装所有插件，exclude_keywords=test,deprecated"
```

### 支持的仓库

- `Fu-Jie/openwebui-extensions` - 默认的官方插件集合
- `iChristGit/OpenWebui-Tools` - 全面的工具和插件集合
- `Haervwe/open-webui-tools` - 专业的工具和实用程序
- `Classic298/open-webui-plugins` - 各种插件实现
- `suurt8ll/open_webui_functions` - 基于函数的插件

## 默认仓库

未指定仓库时，默认使用 `Fu-Jie/openwebui-extensions`。

## 插件检测规则

### Fu-Jie/openwebui-extensions（严格模式）

对于默认仓库，插件必须有：
1. 包含 `class Tools:`、`class Filter:`、`class Pipe:` 或 `class Action:` 的 `.py` 文件
2. 包含 `title:`、`description:` 和 **`openwebui_id:`** 字段的文档字符串
3. 文件名不能以 `_cn` 结尾

### 其他 GitHub 仓库

对于其他仓库：
1. 包含 `class Tools:`、`class Filter:`、`class Pipe:` 或 `class Action:` 的 `.py` 文件
2. 包含 `title:` 和 `description:` 字段的文档字符串

## 配置 (Valves)

| 参数 | 默认值 | 描述 |
| --- | --- | --- |
| `SKIP_KEYWORDS` | `test,verify,example,template,mock` | 要跳过的关键词，用逗号分隔 |
| `TIMEOUT` | `20` | 请求超时时间（秒） |

## 确认超时时间

用户确认对话框的默认超时时间为 **2 分钟（120 秒）**，为用户提供充足的时间来：
- 阅读和查看插件列表
- 做出安装决定
- 处理网络延迟

## 支持

如果这个插件对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 Star，这将是我持续改进的动力，感谢支持。
