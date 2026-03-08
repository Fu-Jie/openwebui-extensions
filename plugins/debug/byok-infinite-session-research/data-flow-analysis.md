# 数据流分析：SDK如何获知用户设计的数据

## 当前数据流（从OpenWebUI → Pipe → SDK）

```
┌─────────────────────┐
│   OpenWebUI UI       │
│  (用户选择模型)      │
└──────────┬──────────┘
           │
           ├─ body.model = "gpt-4"
           ├─ body.messages = [...]
           ├─ __metadata__.base_model_id = ?
           ├─ __metadata__.custom_fields = ?
           └─ __user__.settings = ?
           │
┌──────────▼──────────┐
│  Pipe (github-     │
│   copilot-sdk.py)   │
│                     │
│ 1. 提取model信息    │
│ 2. 应用Valves配置  │
│ 3. 建立SDK会话     │
└──────────┬──────────┘
           │
           ├─ SessionConfig {
           │    model: real_model_id
           │    provider: ProviderConfig (若BYOK)
           │    infinite_sessions: {...}
           │    system_message: {...}
           │    ...
           │  }
           │
┌──────────▼──────────┐
│  Copilot SDK        │
│ (create_session)    │
│                     │
│ 返回:ModelInfo {    │
│   capabilities {    │
│    limits {         │
│      max_context_   │
│      window_tokens  │
│    }               │
│   }                │
│ }                  │
└─────────────────────┘
```

---

## 关键问题：当前的3个瓶颈

### 瓶颈1：用户数据的输入点

**当前支持的输入方式：**

1. **Valves配置（全局 + 用户级）**
   ```python
   # 全局设置（Admin）
   Valves.BYOK_BASE_URL = "https://api.openai.com/v1"
   Valves.BYOK_API_KEY = "sk-..."
   
   # 用户级覆盖
   UserValves.BYOK_API_KEY = "sk-..." (用户自己的key)
   UserValves.BYOK_BASE_URL = "..."
   ```
   
   **问题**：无法为特定的BYOK模型设置上下文窗口大小

2. **__metadata__（来自OpenWebUI）**
   ```python
   __metadata__ = {
       "base_model_id": "...",
       "custom_fields": {...},  # ← 可能包含额外信息
       "tool_ids": [...],
   }
   ```
   
   **问题**：不清楚OpenWebUI是否支持通过metadata传递模型的上下文窗口

3. **body（来自对话请求）**
   ```python
   body = {
       "model": "gpt-4",
       "messages": [...],
       "temperature": 0.7,
       # ← 这里能否添加自定义字段？
   }
   ```

---

### 瓶颈2：模型信息的识别和存储

**当前代码** (line 5905+)：
```python
# 解析用户选择的模型
request_model = body.get("model", "")  # e.g., "gpt-4"
real_model_id = request_model

# 确定实际模型ID
base_model_id = _container_get(__metadata__, "base_model_id", "")

if base_model_id:
    resolved_id = base_model_id  # 使用元数据中的ID
else:
    resolved_id = request_model   # 使用用户选择的ID
```

**问题**：
- ❌ 没有维护一个"模型元数据缓存"
- ❌ 对相同模型的重复请求，每次都需要重新识别
- ❌ 不能为特定模型持久化上下文窗口大小

---

### 瓶颈3：SDK会话配置的构建

**当前实现** (line 5058-5100)：
```python
def _build_session_config(
    self,
    real_model_id,      # ← 模型ID
    system_prompt_content,
    is_streaming=True,
    is_admin=False,
    # ... 其他参数
):
    # 无条件地创建infinite session
    if self.valves.INFINITE_SESSION:
        infinite_session_config = InfiniteSessionConfig(
            enabled=True,
            background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,  # 0.80
            buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,          # 0.95
        )
    
    # ❌ 这里没有查询该模型的实际上下文窗口大小
    # ❌ 无法根据模型的真实限制调整压缩阈值
```

---

## 解决方案：3个数据流改进步骤

### 步骤1：添加模型元数据配置（优先级：高）

在Valves中添加一个**模型元数据映射**：

```python
class Valves(BaseModel):
    # ... 现有配置 ...
    
    # 新增：模型上下文窗口映射 (JSON格式)
    MODEL_CONTEXT_WINDOWS: str = Field(
        default="{}",  # JSON string
        description='Model context window mapping (JSON). Example: {"gpt-4": 8192, "gpt-4-turbo": 128000, "claude-3": 200000}'
    )
    
    # 新增：BYOK模型特定设置 (JSON格式)
    BYOK_MODEL_CONFIG: str = Field(
        default="{}",  # JSON string
        description='BYOK-specific model configuration (JSON). Example: {"gpt-4": {"context_window": 8192, "enable_compression": true}}'
    )
```

**如何使用**：
```python
# Valves中设置
MODEL_CONTEXT_WINDOWS = '{"gpt-4": 8192, "claude-3-5-sonnet": 200000}'

# Pipe中解析
def _get_model_context_window(self, model_id: str) -> Optional[int]:
    """从配置中获取模型的上下文窗口大小"""
    try:
        config = json.loads(self.valves.MODEL_CONTEXT_WINDOWS or "{}")
        return config.get(model_id)
    except:
        return None
```

### 步骤2：建立模型信息缓存（优先级：中）

在Pipe中维护一个模型信息缓存：

```python
class Pipe:
    def __init__(self):
        # ... 现有代码 ...
        self._model_info_cache = {}  # model_id -> ModelInfo
        self._context_window_cache = {}  # model_id -> context_window_tokens

    def _cache_model_info(self, model_id: str, model_info: ModelInfo):
        """缓存SDK返回的模型信息"""
        self._model_info_cache[model_id] = model_info
        if model_info.capabilities and model_info.capabilities.limits:
            self._context_window_cache[model_id] = (
                model_info.capabilities.limits.max_context_window_tokens
            )

    def _get_context_window(self, model_id: str) -> Optional[int]:
        """获取模型的上下文窗口大小（优先级：SDK > Valves配置 > 默认值）"""
        # 1. 优先从SDK缓存获取（最可靠）
        if model_id in self._context_window_cache:
            return self._context_window_cache[model_id]
        
        # 2. 其次从Valves配置获取
        context_window = self._get_model_context_window(model_id)
        if context_window:
            return context_window
        
        # 3. 默认值（未知）
        return None
```

### 步骤3：使用真实的上下文窗口来优化压缩策略（优先级：中）

修改_build_session_config：

```python
def _build_session_config(
    self,
    real_model_id,
    # ... 其他参数 ...
    **kwargs
):
    # 获取模型的真实上下文窗口大小
    actual_context_window = self._get_context_window(real_model_id)
    
    # 只对有明确上下文窗口的模型启用压缩
    infinite_session_config = None
    if self.valves.INFINITE_SESSION and actual_context_window:
        # 现在压缩阈值有了明确的含义
        infinite_session_config = InfiniteSessionConfig(
            enabled=True,
            # 80% of actual context window
            background_compaction_threshold=self.valves.COMPACTION_THRESHOLD,
            # 95% of actual context window
            buffer_exhaustion_threshold=self.valves.BUFFER_THRESHOLD,
        )
        
        await self._emit_debug_log(
            f"Infinite Session: model_context={actual_context_window}tokens, "
            f"compaction_triggers_at={int(actual_context_window * self.valves.COMPACTION_THRESHOLD)}, "
            f"buffer_triggers_at={int(actual_context_window * self.valves.BUFFER_THRESHOLD)}",
            __event_call__,
        )
    elif self.valves.INFINITE_SESSION and not actual_context_window:
        logger.warning(
            f"Infinite Session: Unknown context window for {real_model_id}, "
            f"compression disabled. Set MODEL_CONTEXT_WINDOWS in Valves to enable."
        )
```

---

## 具体的配置示例

### 例子1：用户配置BYOK模型的上下文窗口

**Valves设置**：
```
MODEL_CONTEXT_WINDOWS = {
  "gpt-4": 8192,
  "gpt-4-turbo": 128000,
  "gpt-4o": 128000,
  "claude-3": 200000,
  "claude-3.5-sonnet": 200000,
  "llama-2-70b": 4096
}
```

**效果**：
- Pipe会知道"gpt-4"的上下文是8192 tokens
- 压缩会在 ~6553 tokens (80%) 时触发
- 缓冲会在 ~7782 tokens (95%) 时阻塞

### 例子2：为特定BYOK模型启用/禁用压缩

**Valves设置**：
```
BYOK_MODEL_CONFIG = {
  "gpt-4": {
    "context_window": 8192,
    "enable_infinite_session": true,
    "compaction_threshold": 0.75
  },
  "llama-2-70b": {
    "context_window": 4096,
    "enable_infinite_session": false  # 禁用压缩
  }
}
```

**Pipe逻辑**：
```python
# 检查模型特定的压缩设置
def _get_compression_enabled(self, model_id: str) -> bool:
    try:
        config = json.loads(self.valves.BYOK_MODEL_CONFIG or "{}")
        model_config = config.get(model_id, {})
        return model_config.get("enable_infinite_session", self.valves.INFINITE_SESSION)
    except:
        return self.valves.INFINITE_SESSION
```

---

## 总结：SDK如何获知用户设计的数据

| 来源 | 方式 | 更新 | 示例 |
|------|------|------|------|
| **Valves** | 全局配置 | Admin提前设置 | `MODEL_CONTEXT_WINDOWS` JSON |
| **SDK** | SessionConfig返回 | 每次会话创建 | `model_info.capabilities.limits` |
| **缓存** | Pipe本地存储 | 首次获取后缓存 | `_context_window_cache` |
| **__metadata__** | OpenWebUI传递 | 每次请求随带 | `base_model_id`, custom fields |

**流程**：
1. 用户在Valves中配置 `MODEL_CONTEXT_WINDOWS`
2. Pipe在session创建时获取SDK返回的model_info
3. Pipe缓存上下文窗口大小
4. Pipe根据真实窗口大小调整infinite session的阈值
5. SDK使用正确的压缩策略

这样，**SDK完全知道用户设计的数据**，而无需任何修改SDK本身。
