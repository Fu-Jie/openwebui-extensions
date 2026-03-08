# SDK中的上下文限制信息

## SDK类型定义

### 1. ModelLimits（copilot-sdk/python/copilot/types.py, line 761-789）

```python
@dataclass
class ModelLimits:
    """Model limits"""
    
    max_prompt_tokens: int | None = None           # 最大提示符tokens
    max_context_window_tokens: int | None = None   # 最大上下文窗口tokens
    vision: ModelVisionLimits | None = None        # 视觉相关限制
```

### 2. ModelCapabilities（line 817-843）

```python
@dataclass
class ModelCapabilities:
    """Model capabilities and limits"""
    
    supports: ModelSupports      # 支持的功能（vision, reasoning_effort等）
    limits: ModelLimits          # 上下文和token限制
```

### 3. ModelInfo（line 889-949）

```python
@dataclass
class ModelInfo:
    """Information about an available model"""
    
    id: str
    name: str
    capabilities: ModelCapabilities  # ← 包含limits信息
    policy: ModelPolicy | None = None
    billing: ModelBilling | None = None
    supported_reasoning_efforts: list[str] | None = None
    default_reasoning_effort: str | None = None
```

---

## 关键发现

### ✅ SDK提供的信息
- `model.capabilities.limits.max_context_window_tokens` - 模型的上下文窗口大小
- `model.capabilities.limits.max_prompt_tokens` - 最大提示符tokens

### ❌ OpenWebUI Pipe中的问题
**目前Pipe完全没有使用这些信息！**

在 `github_copilot_sdk.py` 中搜索 `max_context_window`, `capabilities`, `limits` 等，结果为空。

---

## 这对BYOK意味着什么？

### 问题1: BYOK模型的上下文限制未知
```python
# BYOK模型的capabilities来自哪里？
if is_byok_model:
    # ❓ BYOK模型没有能力信息返回吗？
    # ❓ 如何知道它的max_context_window_tokens？
    pass
```

### 问题2: Infinite Session的阈值是硬编码的
```python
COMPACTION_THRESHOLD: float = Field(
    default=0.80,  # 80%时触发后台压缩
    description="Background compaction threshold (0.0-1.0)"
)
BUFFER_THRESHOLD: float = Field(
    default=0.95,  # 95%时阻塞直到压缩完成
    description="Buffer exhaustion threshold (0.0-1.0)"
)

# 但是 0.80 和 0.95 是什么的百分比？
# - 是模型的max_context_window_tokens吗？
# - 还是固定的某个值？
# - BYOK模型的上下文窗口可能完全不同！
```

---

## 改进方向

### 方案A: 利用SDK提供的模型限制信息
```python
# 在获取模型信息时，保存capabilities
self._model_capabilities = model_info.capabilities

# 在初始化infinite session时，使用实际的上下文窗口
if model_info.capabilities.limits.max_context_window_tokens:
    actual_context_window = model_info.capabilities.limits.max_context_window_tokens
    
    # 动态调整压缩阈值而不是固定值
    compaction_threshold = self.valves.COMPACTION_THRESHOLD
    buffer_threshold = self.valves.BUFFER_THRESHOLD
    # 这些现在有了明确的含义：是模型实际上下文窗口大小的百分比
```

### 方案B: BYOK模型的显式配置
如果BYOK模型不提供capabilities信息，需要用户手动设置：

```python
class Valves(BaseModel):
    # ... existing config ...
    
    BYOK_CONTEXT_WINDOW: int = Field(
        default=0,  # 0表示自动检测或禁用compression
        description="Manual context window size for BYOK models (tokens). 0=auto-detect or disabled"
    )
    
    BYOK_INFINITE_SESSION: bool = Field(
        default=False,
        description="Enable infinite sessions for BYOK models (requires BYOK_CONTEXT_WINDOW > 0)"
    )
```

### 方案C: 从会话反馈中学习（最可靠）
```python
# infinite session压缩完成时，获取实际的context window使用情况
# (需要SDK或CLI提供反馈)
```

---

## 建议实施路线

**优先级1（必须）**: 检查BYOK模式下是否能获取capabilities
```python
# 测试代码
if is_byok_model:
    # 发送一个测试请求，看是否能从响应中获取model capabilities
    session = await client.create_session(config=session_config)
    # session是否包含model info？
    # 能否访问session.model_capabilities？
```

**优先级2（重要）**: 如果BYOK没有capabilities，添加手动配置
```python
# 在BYOK配置中添加context_window字段
BYOK_CONTEXT_WINDOW: int = Field(default=0)
```

**优先级3（长期）**: 利用真实的上下文窗口来调整压缩策略
```python
# 而不是单纯的百分比，使用实际的token数
```

---

## 关键问题列表

1. [ ] BYOK模型在create_session后能否获取capabilities信息？
2. [ ] 如果能获取，max_context_window_tokens的值是否准确？
3. [ ] 如果不能获取，是否需要用户手动提供？
4. [ ] 当前的0.80/0.95阈值是否对所有模型都适用？
5. [ ] 不同的BYOK提供商(OpenAI vs Anthropic)的上下文窗口差异有多大？
