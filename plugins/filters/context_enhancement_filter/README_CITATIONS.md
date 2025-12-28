# Citations 处理功能文档

## 概述

`context_enhancement_filter.py` 现在支持自动处理模型响应中的 `citations` 和 `grounding_metadata`，将其转换为 Open WebUI 的标准引用格式，使搜索来源能够在聊天界面中正确展示。

## 支持的数据格式

### 1. Gemini Search 格式

模型响应包含顶层的 `citations` 数组和 `grounding_metadata`：

```json
{
  "id": "chatcmpl-xxx",
  "type": "stream",
  "model": "gemini-3-flash-preview-search",
  "content": "回答内容...",
  "citations": [
    {
      "source": {
        "url": "https://example.com/article",
        "name": "example.com"
      },
      "retrieved_at": "2025-12-27T17:50:03.472550"
    }
  ],
  "grounding_metadata": {
    "web_search_queries": [
      "搜索查询1",
      "搜索查询2"
    ]
  }
}
```

### 2. 嵌套在 messages 中的格式

Citations 数据嵌套在最后一条 assistant 消息中：

```json
{
  "messages": [
    {
      "role": "assistant",
      "content": "回答内容...",
      "citations": [...],
      "grounding_metadata": {...}
    }
  ]
}
```

## 功能特性

### 1. 自动引用提取

插件会自动从以下位置提取 citations：
- 响应体顶层的 `citations` 字段
- 最后一条 assistant 消息中的 `citations` 字段

### 2. 引用格式转换

将模型原始的 citations 格式转换为 Open WebUI 标准格式：

**输入格式：**
```json
{
  "source": {
    "url": "https://example.com",
    "name": "example.com"
  },
  "retrieved_at": "2025-12-27T17:50:03.472550"
}
```

**输出格式：**
```json
{
  "type": "citation",
  "data": {
    "document": ["来源：example.com\n检索时间：2025-12-27T17:50:03.472550"],
    "metadata": [
      {
        "source": "example.com",
        "url": "https://example.com",
        "date_accessed": "2025-12-27T17:50:03.472550",
        "type": "web_search_result"
      }
    ],
    "source": {
      "name": "example.com",
      "url": "https://example.com"
    }
  }
}
```

### 3. 搜索查询展示

如果响应包含 `grounding_metadata.web_search_queries`，会在界面上显示使用的搜索查询：

```
🔍 使用了 4 个搜索查询
```

### 4. 处理状态提示

成功处理 citations 后，会显示状态提示：

```
✓ 已处理 7 个引用来源
```

## 在 Open WebUI 中的展示效果

### 引用链接
每个引用来源会在聊天界面中显示为可点击的链接，用户可以：
- 点击查看原始来源
- 查看检索时间等元数据
- 了解信息的出处

### 搜索查询历史
显示模型使用的搜索查询列表，帮助用户了解：
- 模型如何理解和分解查询
- 执行了哪些搜索操作
- 搜索策略是否合理

## 使用示例

### 示例 1：Gemini Search 模型

当使用支持搜索的 Gemini 模型时：

```python
# 用户提问
"MiniMax 最新的模型是什么？"

# 模型响应会包含 citations
{
  "content": "MiniMax 最新的模型是 M2.1...",
  "citations": [
    {"source": {"url": "https://qbitai.com/...", "name": "qbitai.com"}, ...},
    {"source": {"url": "https://minimax.io/...", "name": "minimax.io"}, ...}
  ]
}

# Open WebUI 界面显示：
# 1. 模型的回答内容
# 2. 可点击的引用链接：qbitai.com, minimax.io 等
# 3. 状态提示：✓ 已处理 7 个引用来源
```

### 示例 2：自定义 Pipe/Filter

如果你的自定义 Pipe 或 Filter 返回包含 citations 的数据：

```python
class CustomPipe:
    def pipe(self, body: dict) -> dict:
        # 执行搜索或检索操作
        search_results = self.perform_search(query)
        
        # 构建响应，包含 citations
        return {
            "messages": [{
                "role": "assistant",
                "content": "基于搜索结果...",
                "citations": [
                    {
                        "source": {"url": url, "name": domain},
                        "retrieved_at": datetime.now().isoformat()
                    }
                    for url, domain in search_results
                ]
            }]
        }
```

`context_enhancement_filter` 会自动处理这些 citations 并在界面中展示。

## 配置说明

### 启用 Filter

1. 在 Open WebUI 中安装 `context_enhancement_filter.py`
2. 确保 Filter 已启用
3. Citations 处理功能自动生效，无需额外配置

### 与其他功能的集成

Citations 处理与 Filter 的其他功能（环境变量注入、内容规范化等）无缝集成：

- **环境变量注入**：在 inlet 阶段处理
- **内容规范化**：在 outlet 阶段处理
- **Citations 处理**：在 outlet 阶段处理（与内容规范化并行）

## 技术实现细节

### 异步处理

Citations 处理使用异步方式，不会阻塞主响应流：

```python
asyncio.create_task(self._process_citations(body, __event_emitter__))
```

### 错误处理

- 完善的异常捕获，确保 citations 处理失败不影响正常响应
- 详细的日志记录，便于问题排查
- 优雅降级：如果处理失败，用户仍能看到模型回答

### 兼容性

- 支持多种 citations 数据格式
- 向后兼容：不包含 citations 的响应不受影响
- 与 Open WebUI 原生 citations 系统完全兼容

## 常见问题

### Q: Citations 没有显示？

**A:** 检查以下几点：
1. 模型响应是否包含 `citations` 字段
2. Filter 是否已启用
3. `__event_emitter__` 是否正常工作
4. 浏览器控制台是否有错误信息

### Q: 如何自定义 citations 展示格式？

**A:** 修改 `_process_citations` 方法中的 `document_text` 构建逻辑：

```python
# 自定义文档文本格式
document_text = f"""
📄 **{source_name}**
🔗 {source_url}
⏰ {retrieved_at}
"""
```

### Q: 可以禁用 citations 处理吗？

**A:** 可以通过以下方式禁用：

1. **临时禁用**：在 outlet 方法中注释掉 citations 处理代码
2. **条件禁用**：添加配置选项到 Valves：

```python
class Valves(BaseModel):
    enable_citations_processing: bool = Field(
        default=True, 
        description="启用 citations 自动处理"
    )
```

## 与 websearch.py 的对比

| 特性 | websearch.py | context_enhancement_filter.py |
|------|--------------|-------------------------------|
| 功能 | 主动执行搜索 | 被动处理已有 citations |
| 时机 | inlet (请求前) | outlet (响应后) |
| 搜索引擎 | SearxNG | 依赖模型自身 |
| 内容注入 | 直接修改用户消息 | 不修改消息 |
| 引用展示 | ✅ 支持 | ✅ 支持 |

**推荐使用场景：**
- 使用支持搜索的模型（如 Gemini Search）：启用 `context_enhancement_filter`
- 使用不支持搜索的模型：启用 `websearch.py`
- 需要自定义搜索源：使用 `websearch.py` 配置 SearxNG

## 未来改进方向

1. **更丰富的元数据展示**
   - 显示网页标题、摘要
   - 展示相关性评分
   - 支持缩略图预览

2. **智能内容提取**
   - 从响应内容中提取被引用的具体段落
   - 高亮显示引用来源对应的文本

3. **引用验证**
   - 检查引用链接的有效性
   - 提供存档链接备份

4. **用户配置选项**
   - 自定义引用展示格式
   - 选择性显示/隐藏某些元数据
   - 引用分组和排序选项

## 参考资源

- [Open WebUI Plugin 开发文档](../../docs/features/plugin/tools/development.mdx)
- [Event Emitter 使用指南](../../docs/features/plugin/development/events.mdx)
- [WebSearch Filter 实现](../websearch/websearch.py)

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个功能！
