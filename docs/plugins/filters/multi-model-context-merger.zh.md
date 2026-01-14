# 多模型上下文合并 (Multi-Model Context Merger)

<span class="category-badge filter">Filter</span>
<span class="version-badge">v0.1.0</span>

自动合并上一轮中多个模型的回答上下文，实现协作问答。

---

## 概述

此过滤器检测上一轮是否由多个模型回复（例如使用“竞技场”模式或选择了多个模型）。它将这些回复合并并作为上下文注入到当前轮次，使下一个模型能够看到其他模型之前所说的内容。

## 功能特性

- :material-merge: **自动合并**: 将多个模型的回复合并为单个上下文块。
- :material-format-list-group: **结构化注入**: 使用类似 XML 的标签 (`<response>`) 分隔不同模型的输出。
- :material-robot-confused: **协作**: 允许模型基于彼此的回答进行构建或评论。

---

## 安装

1. 下载插件文件: [`multi_model_context_merger.py`](https://github.com/Fu-Jie/awesome-openwebui/tree/main/plugins/filters)
2. 上传到 OpenWebUI: **管理员面板** → **设置** → **函数**
3. 启用过滤器。

---

## 使用方法

1. 在聊天中选择 **多个模型** (或使用竞技场模式)。
2. 提问。所有模型都会回答。
3. 提出后续问题。
4. 过滤器会将所有模型之前的回答注入到当前模型的上下文中。
