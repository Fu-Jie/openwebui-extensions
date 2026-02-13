# Context Enhancement（上下文增强）

<span class="category-badge filter">Filter</span>
<span class="version-badge">v0.2</span>

为聊天自动补充上下文信息，让 LLM 回复更相关、更准确。

---

## 概览

Context Enhancement 过滤器会自动为会话补充必要的上下文，使模型回答更加贴切。

## 功能特性

- :material-text-box-plus: **自动增强**：智能添加相关上下文
- :material-clock: **时间感知**：包含当前日期/时间信息
- :material-account: **用户上下文**：加入用户偏好或姓名等信息
- :material-cog: **可定制**：可配置要附加的上下文内容

---

## 安装

1. 下载插件文件：[`context_enhancement_filter.py`](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/context_enhancement_filter)
2. 上传到 OpenWebUI：**Admin Panel** → **Settings** → **Functions**
3. 配置增强选项
4. 启用过滤器

---

## 配置项

| 选项 | 类型 | 默认值 | 说明 |
|--------|------|---------|-------------|
| `include_datetime` | boolean | `true` | 是否添加当前日期时间 |
| `include_user_info` | boolean | `true` | 是否添加用户名和偏好 |
| `custom_context` | string | `""` | 始终附加的自定义上下文 |

---

## 运行要求

!!! note "前置条件"
    - OpenWebUI v0.3.0 及以上

---

## 源码

[:fontawesome-brands-github: 在 GitHub 查看](https://github.com/Fu-Jie/openwebui-extensions/tree/main/plugins/filters/context_enhancement_filter){ .md-button }
