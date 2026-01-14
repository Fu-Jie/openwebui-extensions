# Web Gemini 多模态过滤器

<span class="category-badge filter">Filter</span>
<span class="version-badge">v0.3.2</span>

一个强大的过滤器，为 OpenWebUI 中的任何模型提供多模态能力：PDF、Office、图片、音频、视频等。

---

## 概述

此插件利用 Gemini 作为分析器，为任何模型提供多模态处理能力。它支持 Gemini 模型的直接文件处理，以及其他模型（如 DeepSeek, Llama）的“分析器模式”，即由 Gemini 分析文件并将结果注入上下文。

## 功能特性

- :material-file-document-multiple: **多模态支持**: 处理 PDF, Word, Excel, PowerPoint, EPUB, MP3, MP4 和图片。
- :material-router-network: **智能路由**:
    - **直连模式 (Direct Mode)**: 对于 Gemini 模型，文件直接传递（原生多模态）。
    - **分析器模式 (Analyzer Mode)**: 对于非 Gemini 模型，文件由 Gemini 分析，结果注入为上下文。
- :material-history: **持久上下文**: 利用 OpenWebUI 的 Chat ID 跨多轮对话维护会话历史。
- :material-database-check: **数据库去重**: 自动记录已分析文件的哈希值，防止重复上传和分析。
- :material-subtitles: **字幕增强**: 针对视频/音频上传的专用模式，生成高质量 SRT 字幕。

---

## 安装

1. 下载插件文件: [`web_gemini_multimodel.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/filters/web_gemini_multimodel_filter)
2. 上传到 OpenWebUI: **管理员面板** → **设置** → **函数**
3. 配置 Gemini Adapter URL 和其他设置。
4. 启用过滤器。

---

## 配置

| 选项 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `gemini_adapter_url` | string | `http://...` | Gemini Adapter 服务的 URL |
| `target_model_keyword` | string | `"webgemini"` | 识别 Gemini 模型的关键字 |
| `mode` | string | `"auto"` | `auto` (自动), `direct` (直连), 或 `analyzer` (分析器) |
| `analyzer_base_model_id` | string | `"gemini-3.0-pro"` | 用于文档分析的模型 |
| `subtitle_keywords` | string | `"字幕,srt"` | 触发字幕流程的关键字 |

---

## 使用方法

1. 在聊天中 **上传文件** (PDF, 图片, 视频等)。
2. 关于文件 **提问**。
3. 插件会自动处理文件并为所选模型提供上下文。
