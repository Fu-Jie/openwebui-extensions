"""
title: 📊 信息图转 Markdown
author: Fu-Jie
version: 1.0.0
description: AI 生成信息图语法，前端渲染 SVG 并转换为 Markdown 图片格式嵌入消息。支持 AntV Infographic 模板。
"""

import time
import json
import logging
import re
from typing import Optional, Callable, Awaitable, Any, Dict
from pydantic import BaseModel, Field
from fastapi import Request
from datetime import datetime

from open_webui.utils.chat import generate_chat_completion
from open_webui.models.users import Users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =================================================================
# LLM 提示词
# =================================================================

SYSTEM_PROMPT_INFOGRAPHIC = """
你是一位专业的信息图设计专家，能够分析用户提供的文本内容并将其转换为 AntV Infographic 语法格式。

## 信息图语法规范

信息图语法是一种类似 Mermaid 的声明式语法，用于描述信息图模板、数据和主题。

### 语法规则
- 入口使用 `infographic <模板名>`
- 键值对用空格分隔，**绝对不允许使用冒号**
- 使用两个空格缩进
- 对象数组使用 `-` 加换行

⚠️ **重要警告：这不是 YAML 格式！**
- ❌ 错误：`children:` `items:` `data:`（带冒号）
- ✅ 正确：`children` `items` `data`（不带冒号）

### 模板库与选择指南

根据内容结构选择最合适的模板：

#### 1. 列表与层级
- **列表**：`list-grid`（网格卡片）、`list-vertical`（垂直列表）
- **树形**：`tree-vertical`（垂直树）、`tree-horizontal`（水平树）
- **思维导图**：`mindmap`（思维导图）

#### 2. 序列与关系
- **流程**：`sequence-roadmap`（路线图）、`sequence-zigzag`（折线流程）
- **关系**：`relation-sankey`（桑基图）、`relation-circle`（圆形关系）

#### 3. 对比与分析
- **对比**：`compare-binary`（二元对比）
- **分析**：`compare-swot`（SWOT 分析）、`quadrant-quarter`（象限图）

#### 4. 图表与数据
- **图表**：`chart-bar`、`chart-column`、`chart-line`、`chart-pie`、`chart-doughnut`、`chart-area`

### 数据结构示例

#### A. 标准列表/树形
```infographic
infographic list-grid
data
  title 项目模块
  items
    - label 模块 A
      desc 模块 A 的描述
    - label 模块 B
      desc 模块 B 的描述
```

#### B. 二元对比
```infographic
infographic compare-binary
data
  title 优势与劣势
  items
    - label 优势
      children
        - label 研发能力强
          desc 技术领先
    - label 劣势
      children
        - label 品牌曝光弱
          desc 营销不足
```

#### C. 图表
```infographic
infographic chart-bar
data
  title 季度收入
  items
    - label Q1
      value 120
    - label Q2
      value 150
```

### 常用数据字段
- `label`：主标题/标签（必填）
- `desc`：描述文字（`list-grid` 最多 30 个中文字符）
- `value`：数值（用于图表）
- `children`：嵌套项

## 输出要求
1. **语言**：使用用户的语言输出内容。
2. **格式**：用 ```infographic ... ``` 包裹输出。
3. **无冒号**：键后面不要使用冒号。
4. **缩进**：使用 2 个空格。
"""

USER_PROMPT_GENERATE = """
请分析以下文本内容，将其核心信息转换为 AntV Infographic 语法格式。

---
**用户上下文：**
用户名：{user_name}
当前时间：{current_date_time_str}
用户语言：{user_language}
---

**文本内容：**
{long_text_content}

请根据文本特征选择最合适的信息图模板，输出标准的信息图语法。

**重要提示：** 
- 如果使用 `list-grid` 格式，确保每个卡片的 `desc` 描述限制在 **最多 30 个中文字符**。
- 描述应简洁，突出重点。
"""


class Action:
    class Valves(BaseModel):
        SHOW_STATUS: bool = Field(
            default=True, description="在聊天界面显示操作状态更新。"
        )
        MODEL_ID: str = Field(
            default="",
            description="用于文本分析的 LLM 模型 ID。留空则使用当前对话模型。",
        )
        MIN_TEXT_LENGTH: int = Field(
            default=50,
            description="信息图分析所需的最小文本长度（字符数）。",
        )
        MESSAGE_COUNT: int = Field(
            default=1,
            description="用于生成的最近消息数量。",
        )
        SVG_WIDTH: int = Field(
            default=800,
            description="生成的 SVG 宽度（像素）。",
        )
        EXPORT_FORMAT: str = Field(
            default="svg",
            description="导出格式：'svg' 或 'png'。",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _extract_chat_id(self, body: dict, metadata: Optional[dict]) -> str:
        """从 body 或 metadata 中提取 chat_id"""
        if isinstance(body, dict):
            chat_id = body.get("chat_id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()

            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                chat_id = body_metadata.get("chat_id")
                if isinstance(chat_id, str) and chat_id.strip():
                    return chat_id.strip()

        if isinstance(metadata, dict):
            chat_id = metadata.get("chat_id")
            if isinstance(chat_id, str) and chat_id.strip():
                return chat_id.strip()

        return ""

    def _extract_message_id(self, body: dict, metadata: Optional[dict]) -> str:
        """从 body 或 metadata 中提取 message_id"""
        if isinstance(body, dict):
            message_id = body.get("id")
            if isinstance(message_id, str) and message_id.strip():
                return message_id.strip()

            body_metadata = body.get("metadata", {})
            if isinstance(body_metadata, dict):
                message_id = body_metadata.get("message_id")
                if isinstance(message_id, str) and message_id.strip():
                    return message_id.strip()

        if isinstance(metadata, dict):
            message_id = metadata.get("message_id")
            if isinstance(message_id, str) and message_id.strip():
                return message_id.strip()

        return ""

    def _extract_infographic_syntax(self, llm_output: str) -> str:
        """从 LLM 输出中提取信息图语法"""
        match = re.search(r"```infographic\s*(.*?)\s*```", llm_output, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            logger.warning("LLM 输出未遵循预期格式，将整个输出作为语法处理。")
            return llm_output.strip()

    def _extract_text_content(self, content) -> str:
        """从消息内容中提取文本，支持多模态格式"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    text_parts.append(item)
            return "\n".join(text_parts)
        return str(content) if content else ""

    async def _emit_status(self, emitter, description: str, done: bool = False):
        """发送状态更新事件"""
        if self.valves.SHOW_STATUS and emitter:
            await emitter(
                {"type": "status", "data": {"description": description, "done": done}}
            )

    def _generate_js_code(
        self,
        unique_id: str,
        chat_id: str,
        message_id: str,
        infographic_syntax: str,
        svg_width: int,
        export_format: str,
    ) -> str:
        """生成用于前端 SVG 渲染的 JavaScript 代码"""
        
        # 转义语法以便嵌入 JS
        syntax_escaped = (
            infographic_syntax
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
            .replace("</script>", "<\\/script>")
        )
        
        # 模板映射
        template_mapping_js = """
        const TEMPLATE_MAPPING = {
            'list-grid': 'list-grid-compact-card',
            'list-vertical': 'list-column-simple-vertical-arrow',
            'tree-vertical': 'hierarchy-tree-tech-style-capsule-item',
            'tree-horizontal': 'hierarchy-tree-lr-tech-style-capsule-item',
            'mindmap': 'hierarchy-mindmap-branch-gradient-capsule-item',
            'sequence-roadmap': 'sequence-roadmap-vertical-simple',
            'sequence-zigzag': 'sequence-horizontal-zigzag-simple',
            'sequence-horizontal': 'sequence-horizontal-zigzag-simple',
            'relation-sankey': 'relation-sankey-simple',
            'relation-circle': 'relation-circle-icon-badge',
            'compare-binary': 'compare-binary-horizontal-simple-vs',
            'compare-swot': 'compare-swot',
            'quadrant-quarter': 'quadrant-quarter-simple-card',
            'statistic-card': 'list-grid-compact-card',
            'chart-bar': 'chart-bar-plain-text',
            'chart-column': 'chart-column-simple',
            'chart-line': 'chart-line-plain-text',
            'chart-area': 'chart-area-simple',
            'chart-pie': 'chart-pie-plain-text',
            'chart-doughnut': 'chart-pie-donut-plain-text'
        };
        """
        
        return f"""
(async function() {{
    const uniqueId = "{unique_id}";
    const chatId = "{chat_id}";
    const messageId = "{message_id}";
    const svgWidth = {svg_width};
    const exportFormat = "{export_format}";
    
    console.log("[信息图 Markdown] 开始渲染...");
    console.log("[信息图 Markdown] chatId:", chatId, "messageId:", messageId);
    
    try {{
        // 加载 AntV Infographic（如果尚未加载）
        if (typeof AntVInfographic === 'undefined') {{
            console.log("[信息图 Markdown] 正在加载 AntV Infographic 库...");
            await new Promise((resolve, reject) => {{
                const script = document.createElement('script');
                script.src = 'https://unpkg.com/@antv/infographic@latest/dist/infographic.min.js';
                script.onload = resolve;
                script.onerror = reject;
                document.head.appendChild(script);
            }});
            console.log("[信息图 Markdown] 库加载完成。");
        }}
        
        const {{ Infographic }} = AntVInfographic;
        
        // 获取信息图语法
        let syntaxContent = `{syntax_escaped}`;
        console.log("[信息图 Markdown] 原始语法:", syntaxContent.substring(0, 200) + "...");
        
        // 清理语法
        const backtick = String.fromCharCode(96);
        const prefix = backtick + backtick + backtick + 'infographic';
        const simplePrefix = backtick + backtick + backtick;
        
        if (syntaxContent.toLowerCase().startsWith(prefix)) {{
            syntaxContent = syntaxContent.substring(prefix.length).trim();
        }} else if (syntaxContent.startsWith(simplePrefix)) {{
            syntaxContent = syntaxContent.substring(simplePrefix.length).trim();
        }}
        
        if (syntaxContent.endsWith(simplePrefix)) {{
            syntaxContent = syntaxContent.substring(0, syntaxContent.length - simplePrefix.length).trim();
        }}
        
        // 修复关键字后的冒号
        syntaxContent = syntaxContent.replace(/^(data|items|children|theme|config):/gm, '$1');
        syntaxContent = syntaxContent.replace(/(\\s)(children|items):/g, '$1$2');
        
        // 确保有 infographic 前缀
        if (!syntaxContent.trim().toLowerCase().startsWith('infographic')) {{
            syntaxContent = 'infographic list-grid\\n' + syntaxContent;
        }}
        
        // 应用模板映射
        {template_mapping_js}
        
        for (const [key, value] of Object.entries(TEMPLATE_MAPPING)) {{
            const regex = new RegExp(`infographic\\\\s+${{key}}(?=\\\\s|$)`, 'i');
            if (regex.test(syntaxContent)) {{
                console.log(`[信息图 Markdown] 自动映射: ${{key}} -> ${{value}}`);
                syntaxContent = syntaxContent.replace(regex, `infographic ${{value}}`);
                break;
            }}
        }}
        
        console.log("[信息图 Markdown] 清理后语法:", syntaxContent.substring(0, 200) + "...");
        
        // 创建离屏容器
        const container = document.createElement('div');
        container.id = 'infographic-offscreen-' + uniqueId;
        container.style.cssText = 'position:absolute;left:-9999px;top:-9999px;width:' + svgWidth + 'px;';
        document.body.appendChild(container);
        
        // 创建并渲染信息图
        const instance = new Infographic({{
            container: '#' + container.id,
            width: svgWidth,
            padding: 24,
        }});
        
        console.log("[信息图 Markdown] 正在渲染信息图...");
        instance.render(syntaxContent);
        
        // 等待渲染完成并导出
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        let dataUrl;
        if (exportFormat === 'png') {{
            dataUrl = await instance.toDataURL({{ type: 'png', dpr: 2 }});
        }} else {{
            dataUrl = await instance.toDataURL({{ type: 'svg', embedResources: true }});
        }}
        
        console.log("[信息图 Markdown] Data URL 已生成，长度:", dataUrl.length);
        
        // 清理
        instance.destroy();
        document.body.removeChild(container);
        
        // 生成 Markdown 图片
        const markdownImage = `![📊 AI 生成的信息图](${{dataUrl}})`;
        
        // 通过 API 更新消息
        if (chatId && messageId) {{
            const token = localStorage.getItem("token");
            
            // 获取当前消息内容
            const getResponse = await fetch(`/api/v1/chats/${{chatId}}`, {{
                method: "GET",
                headers: {{ "Authorization": `Bearer ${{token}}` }}
            }});
            
            if (!getResponse.ok) {{
                throw new Error("获取对话数据失败: " + getResponse.status);
            }}
            
            const chatData = await getResponse.json();
            let originalContent = "";
            
            if (chatData.chat && chatData.chat.messages) {{
                const targetMsg = chatData.chat.messages.find(m => m.id === messageId);
                if (targetMsg && targetMsg.content) {{
                    originalContent = targetMsg.content;
                }}
            }}
            
            // 移除已有的信息图图片
            const infographicPattern = /\\n*!\\[📊[^\\]]*\\]\\(data:image\\/[^)]+\\)/g;
            let cleanedContent = originalContent.replace(infographicPattern, "");
            cleanedContent = cleanedContent.replace(/\\n{{3,}}/g, "\\n\\n").trim();
            
            // 追加新图片
            const newContent = cleanedContent + "\\n\\n" + markdownImage;
            
            // 更新消息
            const updateResponse = await fetch(`/api/v1/chats/${{chatId}}/messages/${{messageId}}/event`, {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${{token}}`
                }},
                body: JSON.stringify({{
                    type: "chat:message",
                    data: {{ content: newContent }}
                }})
            }});
            
            if (updateResponse.ok) {{
                console.log("[信息图 Markdown] ✅ 消息更新成功！");
            }} else {{
                console.error("[信息图 Markdown] API 错误:", updateResponse.status);
            }}
        }} else {{
            console.warn("[信息图 Markdown] ⚠️ 缺少 chatId 或 messageId");
        }}
        
    }} catch (error) {{
        console.error("[信息图 Markdown] 错误:", error);
    }}
}})();
"""

    async def action(
        self,
        body: dict,
        __user__: dict = None,
        __event_emitter__=None,
        __event_call__: Optional[Callable[[Any], Awaitable[None]]] = None,
        __metadata__: Optional[dict] = None,
        __request__: Request = None,
    ) -> dict:
        """
        使用 AntV 生成信息图并作为 Markdown 图片嵌入。
        """
        logger.info("动作：信息图转 Markdown 开始")

        # 获取用户信息
        if isinstance(__user__, (list, tuple)):
            user_language = __user__[0].get("language", "zh") if __user__ else "zh"
            user_name = __user__[0].get("name", "用户") if __user__[0] else "用户"
            user_id = __user__[0].get("id", "unknown_user") if __user__ else "unknown_user"
        elif isinstance(__user__, dict):
            user_language = __user__.get("language", "zh")
            user_name = __user__.get("name", "用户")
            user_id = __user__.get("id", "unknown_user")
        else:
            user_language = "zh"
            user_name = "用户"
            user_id = "unknown_user"

        # 获取当前时间
        now = datetime.now()
        current_date_time_str = now.strftime("%Y-%m-%d %H:%M:%S")

        try:
            messages = body.get("messages", [])
            if not messages:
                raise ValueError("没有可用的消息。")

            # 获取最近的消息
            message_count = min(self.valves.MESSAGE_COUNT, len(messages))
            recent_messages = messages[-message_count:]

            # 聚合内容
            aggregated_parts = []
            for msg in recent_messages:
                text_content = self._extract_text_content(msg.get("content"))
                if text_content:
                    aggregated_parts.append(text_content)

            if not aggregated_parts:
                raise ValueError("消息中未找到文本内容。")

            long_text_content = "\n\n---\n\n".join(aggregated_parts)

            # 移除已有的 HTML 块
            parts = re.split(r"```html.*?```", long_text_content, flags=re.DOTALL)
            clean_content = ""
            for part in reversed(parts):
                if part.strip():
                    clean_content = part.strip()
                    break

            if not clean_content:
                clean_content = long_text_content.strip()

            # 检查最小长度
            if len(clean_content) < self.valves.MIN_TEXT_LENGTH:
                await self._emit_status(
                    __event_emitter__,
                    f"⚠️ 内容太短（{len(clean_content)} 字符），至少需要 {self.valves.MIN_TEXT_LENGTH} 字符",
                    True,
                )
                return body

            await self._emit_status(__event_emitter__, "📊 正在分析内容...", False)

            # 通过 LLM 生成信息图语法
            formatted_user_prompt = USER_PROMPT_GENERATE.format(
                user_name=user_name,
                current_date_time_str=current_date_time_str,
                user_language=user_language,
                long_text_content=clean_content,
            )

            target_model = self.valves.MODEL_ID or body.get("model")

            llm_payload = {
                "model": target_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_INFOGRAPHIC},
                    {"role": "user", "content": formatted_user_prompt},
                ],
                "stream": False,
            }

            user_obj = Users.get_user_by_id(user_id)
            if not user_obj:
                raise ValueError(f"无法获取用户对象：{user_id}")

            await self._emit_status(__event_emitter__, "📊 AI 正在生成信息图语法...", False)

            llm_response = await generate_chat_completion(__request__, llm_payload, user_obj)

            if not llm_response or "choices" not in llm_response or not llm_response["choices"]:
                raise ValueError("无效的 LLM 响应。")

            assistant_content = llm_response["choices"][0]["message"]["content"]
            infographic_syntax = self._extract_infographic_syntax(assistant_content)

            logger.info(f"生成的语法：{infographic_syntax[:200]}...")

            # 提取 API 回调所需的 ID
            chat_id = self._extract_chat_id(body, __metadata__)
            message_id = self._extract_message_id(body, __metadata__)
            unique_id = f"ig_{int(time.time() * 1000)}"

            await self._emit_status(__event_emitter__, "📊 正在渲染 SVG...", False)

            # 执行 JS 进行渲染和嵌入
            if __event_call__:
                js_code = self._generate_js_code(
                    unique_id=unique_id,
                    chat_id=chat_id,
                    message_id=message_id,
                    infographic_syntax=infographic_syntax,
                    svg_width=self.valves.SVG_WIDTH,
                    export_format=self.valves.EXPORT_FORMAT,
                )

                await __event_call__(
                    {
                        "type": "execute",
                        "data": {"code": js_code},
                    }
                )

            await self._emit_status(__event_emitter__, "✅ 信息图生成完成！", True)
            logger.info("信息图转 Markdown 完成")

        except Exception as e:
            error_message = f"信息图生成失败：{str(e)}"
            logger.error(error_message, exc_info=True)
            await self._emit_status(__event_emitter__, f"❌ {error_message}", True)

        return body
