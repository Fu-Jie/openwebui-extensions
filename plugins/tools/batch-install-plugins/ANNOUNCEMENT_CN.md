# 🎉 Batch Install Plugins v1.1.0

## 标题
**为 OpenWebUI 批量安装带来可勾选的交互式插件选择器**

## 前言
批量安装不应该是“全装或不装”的二选一。现在，**Batch Install Plugins from GitHub** v1.1.0 新增了基于浏览器的交互式选择对话框，用户可以先查看过滤后的插件列表，再勾选真正要安装的插件，然后才开始调用安装 API。

## 核心特性

### 🚀 交互式插件选择
- 基于 OpenWebUI 的 `execute` 事件打开自定义浏览器选择对话框
- 显示带复选框、类型筛选、关键词搜索、插件描述和仓库信息的过滤结果
- 只安装用户保留勾选的插件

### ✅ 智能安全保障
- 用更丰富的选择流程替代基础 confirmation 事件
- 用户无需改写请求，也能取消勾选不想安装的插件
- 不再显示多余的“复制 exclude_keywords”提示
- 自动排除工具自身，避免重复安装

### 🌍 多仓库支持
支持从**任意公开 GitHub 仓库**安装插件，包括你自己的社区合集：
- 每次请求处理一个仓库，需要时可再次调用工具来组合多个来源
- **默认**：Fu-Jie/openwebui-extensions（我的个人合集）
- 支持公开仓库，格式为 `owner/repo`
- 混合搭配：先从我的合集安装，再通过后续调用添加社区合集

### 🔧 容器友好
- 自动处理容器部署中的端口映射问题
- 智能降级：主连接失败时自动重试 localhost:8080
- 丰富的调试日志便于故障排除

### 🌐 全球化支持
- 完整支持 11 种语言
- 所有错误提示本地化且用户友好
- 跨不同部署场景无缝运行

## 工作流程：交互式安装

每次请求处理一个仓库。如需组合多个仓库，请在上一次安装完成后再发起下一次请求。

1. **先从我的合集开始**
   ```
   "安装 Fu-Jie/openwebui-extensions 中的所有插件"
   ```
   查看选择对话框，保留想安装的勾选项后开始安装。

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

4. **使用你自己的公开仓库**
   ```
   "从 your-username/your-collection 安装所有插件"
   ```
   支持任何公开 GitHub 仓库，格式为 `owner/repo`。

## 热门社区合集

这些社区精选都已准备好安装：

#### **iChristGit/OpenWebui-Tools**
包含各种工具和插件的综合集合。

#### **Haervwe/open-webui-tools**
专业工具和实用程序，扩展 OpenWebUI 功能。

#### **Classic298/open-webui-plugins**
多样化的插件实现，满足不同场景。

#### **suurt8ll/open_webui_functions**
基于函数的插件，用于自定义集成。

#### **rbb-dev/Open-WebUI-OpenRouter-pipe**
OpenRouter API pipe 集成，提供高级模型访问。

## 使用示例

下面每一行都是一次独立请求：

```
# 先从我的合集开始
"安装所有插件"

# 在下一次请求中加入社区插件
"从 iChristGit/OpenWebui-Tools 安装所有插件"

# 从其他仓库只安装某一种类型
"从 Haervwe/open-webui-tools 仅安装 tool 插件"

# 继续补充你的插件组合
"从 Classic298/open-webui-plugins 安装仅 action 插件"

# 过滤不想安装的插件
"从 Haervwe/open-webui-tools 安装所有插件，exclude_keywords=test,deprecated"

# 从你自己的公开仓库安装
"从 your-username/my-plugin-collection 安装所有插件"
```

## 技术亮点

- **异步架构**：非阻塞 I/O，性能更优
- **httpx 集成**：现代化异步 HTTP 客户端，包含超时保护
- **选择性安装流程**：安装循环只会处理用户最终勾选的插件子集
- **完整事件支持**：正确处理 OpenWebUI `execute` 事件，并保留回退行为

## 安装方法

1. 打开 OpenWebUI → 工作区 > 工具
2. 从市场安装 **Batch Install Plugins from GitHub**
3. 为你的模型/对话启用此工具
4. 开始使用，比如说"安装所有插件"

## 相关链接

- **GitHub 仓库**：https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/tools/batch-install-plugins
- **发布说明**：https://github.com/Fu-Jie/openwebui-extensions/blob/main/plugins/tools/batch-install-plugins/v1.1.0_CN.md

## 社区支持

如果这个工具对你有帮助，欢迎到 [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions) 点个 ⭐ — 这将是我们持续改进的动力！

**感谢你支持 OpenWebUI 社区！🙏**
