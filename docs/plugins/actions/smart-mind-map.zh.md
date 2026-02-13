# Smart Mind Map（智能思维导图）

<span class="category-badge action">Action</span>
<span class="version-badge">v0.9.2</span>

智能分析文本内容，生成交互式思维导图，帮助你更直观地理解信息结构。

---

## 概览

Smart Mind Map 会将文本转换成漂亮的交互式思维导图。插件会用 AI 分析内容结构，生成层级化的可视化，帮助快速梳理复杂信息。

## 功能特性

- :material-brain: **LLM 分析**：可配置模型，提取核心概念与层级
- :material-gesture-swipe: **丰富控制**：缩放/重置、展开层级（全部/2/3 级）与全屏
- :material-palette: **主题感知**：自动检测 OpenWebUI 亮/暗色主题并支持手动切换
- :material-download: **一键导出**：下载高分辨率 PNG、复制 SVG 或 Markdown
- :material-translate: **多语言**：输出语言与输入文本一致

---

## 安装

1. 下载插件文件：[`smart_mind_map.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/actions/smart-mind-map)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**（Actions）
3. 启用插件，并可在设置中允许 iframe same-origin 以启用主题自动检测

---

## 使用方法

1. 在聊天设置中启用 **Smart Mind Map**，提供不少于约 100 字符的文本
2. 点击消息操作栏中的 **Mind Map** 动作按钮触发生成
3. 交互使用：
   - **缩放与重置**：滚轮或使用 + / - / ↻ 控制
   - **展开层级**：切换“全部 / 2 级 / 3 级”
   - **主题与全屏**：手动切换亮/暗色或进入全屏
4. 一键导出：**PNG**、**复制 SVG**、**复制 Markdown**

---

## 配置项

| 选项 | 类型 | 默认值 | 说明 |
|--------|------|---------|-------------|
| `SHOW_STATUS` | boolean | `true` | 是否在聊天中显示状态更新 |
| `MODEL_ID` | string | `""` | 内置 LLM 模型 ID（留空使用当前聊天模型） |
| `MIN_TEXT_LENGTH` | integer | `100` | 开始分析所需的最少字符数 |
| `CLEAR_PREVIOUS_HTML` | boolean | `false` | 生成新导图时是否清除之前的插件 HTML |
| `MESSAGE_COUNT` | integer | `1` | 用于生成的最近消息数量（1–5） |

---

## 输出示例

插件会在聊天中嵌入交互式 HTML 思维导图：

```
📊 Mind Map Generated
├── Main Topic
│   ├── Subtopic 1
│   │   ├── Detail A
│   │   └── Detail B
│   ├── Subtopic 2
│   └── Subtopic 3
└── Related Concepts
```

---

## 运行要求

!!! note "前置条件"
    - OpenWebUI v0.3.0 及以上
    - 无需额外 Python 依赖
    - 如需自动匹配主题/提高 PNG 导出准确性，请在 **User Settings → Interface → Artifacts** 中允许 iframe same-origin 访问

---

## 常见问题

??? question "思维导图不显示？"
    - 确认输入文本达到 `MIN_TEXT_LENGTH`
    - 确保已配置可用的 `MODEL_ID`（或留空使用当前模型）
    - 启用插件后刷新页面再试

??? question "主题不匹配或 PNG 为空白？"
    - 在设置中开启 iframe same-origin 以读取父页面主题
    - 等待导图完全渲染后再导出

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/actions/smart-mind-map){ .md-button }
