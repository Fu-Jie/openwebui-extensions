# 信息图 - OpenWebUI Action 插件

将文本内容智能转换为美观的信息图，基于蚂蚁集团 AntV Infographic 引擎。

## 功能特性

- 🤖 **AI 驱动**: 使用 LLM 自动分析文本内容并生成信息图语法
- 📊 **多种模板**: 支持列表、流程、层级等多种信息图类型
- 🎨 **自动图标**: 使用 `ref:search` 语法自动匹配高质量图标
- 💾 **多格式导出**: 支持下载 SVG、PNG 和独立 HTML 文件
- 🎯 **零配置**: 开箱即用，无需额外设置

## 安装

1. 将 `信息图.py` 文件复制到 Open WebUI 的插件目录：
   ```
   plugins/actions/infographic/
   ```

2. 重启 Open WebUI 或在管理界面重新加载插件

3. 在聊天界面的 Action 菜单中即可看到 "信息图" 选项

## 使用方法

1. 在聊天框输入需要可视化的文本内容（建议 100 字符以上）
2. 点击 "信息图" Action 按钮
3. AI 将自动分析文本并生成信息图
4. 可以下载 SVG、PNG 或 HTML 格式的文件

### 示例文本

```
我们的产品开发流程包括三个主要阶段：
1. 需求分析 - 收集和分析用户需求，确定产品方向
2. 设计开发 - 完成 UI/UX 设计和前后端开发
3. 测试上线 - 进行质量验证并正式发布
```

## 配置选项（Valves）

- **SHOW_STATUS**: 是否显示操作状态更新（默认: True）
- **MODEL_ID**: 用于分析的 LLM 模型 ID（默认: 使用当前对话模型）
- **MIN_TEXT_LENGTH**: 最小文本长度要求（默认: 100 字符）
- **CLEAR_PREVIOUS_HTML**: 是否清除之前的插件输出（默认: False）

## 支持的信息图类型

插件会根据文本内容自动选择最合适的模板：

- **列表型**: `list-row-horizontal-icon-arrow`, `list-grid`
- **层级型**: `tree-vertical`, `tree-horizontal`

## 技术栈

- **后端**: Python, OpenWebUI Action API
- **前端**: AntV Infographic (CDN)
- **AI**: 自定义提示词工程

## 许可证

MIT License

## 致谢

- [AntV Infographic](https://infographic.antv.vision/) - 信息图渲染引擎
- [Open WebUI](https://github.com/open-webui/open-webui) - AI 聊天界面
