# 精读 (Deep Dive)

<span class="category-badge action">Action</span>
<span class="version-badge">v1.0.0</span>

全方位的思维透镜 —— 从背景全景到逻辑脉络，从深度洞察到行动路径。

---

## 概述

精读插件改变了您理解复杂内容的方式，通过结构化的思维过程引导您进行深度分析。它不仅仅是摘要，而是从四个阶段解构内容：

- **🔍 全景 (The Context)**: 情境与背景的高层级全景视图
- **🧠 脉络 (The Logic)**: 解构底层推理逻辑与思维模型
- **💎 洞察 (The Insight)**: 提取非显性价值与隐藏含义
- **🚀 路径 (The Path)**: 具体的、按优先级排列的战略行动

## 功能特性

- :material-brain: **思维链**: 完整的结构化分析过程
- :material-eye: **深度理解**: 揭示隐藏的假设和思维盲点
- :material-lightbulb-on: **洞察提取**: 发现"原来如此"的时刻
- :material-rocket-launch: **行动导向**: 将深度理解转化为可执行步骤
- :material-theme-light-dark: **主题自适应**: 自动适配 OpenWebUI 深色/浅色主题
- :material-translate: **多语言**: 以用户偏好语言输出

---

## 安装

1. 下载插件文件: [`deep_dive_cn.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/actions/deep-dive)
2. 上传到 OpenWebUI: **管理面板** → **设置** → **Functions**
3. 启用插件

---

## 使用方法

1. 在聊天中提供任何长文本、文章或会议记录
2. 点击消息操作栏中的 **精读** 按钮
3. 沿着视觉时间轴从"全景"探索到"路径"

---

## 配置参数

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `SHOW_STATUS` | boolean | `true` | 处理过程中是否显示状态更新 |
| `MODEL_ID` | string | `""` | 用于分析的 LLM 模型（空 = 当前模型） |
| `MIN_TEXT_LENGTH` | integer | `200` | 分析所需的最小文本长度 |
| `CLEAR_PREVIOUS_HTML` | boolean | `true` | 是否清除之前的插件结果 |
| `MESSAGE_COUNT` | integer | `1` | 要分析的最近消息数量 |

---

## 主题支持

精读插件自动适配 OpenWebUI 的深色/浅色主题：

- 从父文档 `<meta name="theme-color">` 标签检测主题
- 回退到 `html/body` 的 class 或 `data-theme` 属性
- 最后使用系统偏好 `prefers-color-scheme: dark`

!!! tip "最佳效果"
    请在 OpenWebUI 中启用 **iframe Sandbox Allow Same Origin**：
    **设置** → **界面** → **Artifacts** → 勾选 **iframe Sandbox Allow Same Origin**

---

## 输出示例

插件生成精美的结构化时间轴：

```
┌─────────────────────────────────────┐
│  📖 精读分析报告                     │
│  👤 用户  📅 日期  📊 字数           │
├─────────────────────────────────────┤
│  🔍 阶段 01: 全景 (The Context)      │
│  [高层级全景视图内容]                 │
│                                     │
│  🧠 阶段 02: 脉络 (The Logic)        │
│  • 推理结构分析...                   │
│  • 隐藏假设识别...                   │
│                                     │
│  💎 阶段 03: 洞察 (The Insight)      │
│  • 非显性价值提取...                 │
│  • 思维盲点揭示...                   │
│                                     │
│  🚀 阶段 04: 路径 (The Path)         │
│  ▸ 优先级行动 1...                   │
│  ▸ 优先级行动 2...                   │
└─────────────────────────────────────┘
```

---

## 系统要求

!!! note "前提条件"
    - OpenWebUI v0.3.0 或更高版本
    - 使用当前活跃的 LLM 模型进行分析
    - 需要 `markdown` Python 包

---

## 源代码

[:fontawesome-brands-github: 在 GitHub 上查看](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/actions/deep-dive){ .md-button }
