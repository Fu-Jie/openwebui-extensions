# OpenWebUI Skills 管理工具

**Author:** [Fu-Jie](https://github.com/Fu-Jie/openwebui-extensions) | **Version:** 0.2.1 | **Project:** [OpenWebUI Extensions](https://github.com/Fu-Jie/openwebui-extensions)

一个可跨模型使用的 OpenWebUI 原生 Tool 插件，用于管理 Workspace Skills。

## 最新更新

- `install_skill` 新增 GitHub 技能目录自动发现（例如 `.../tree/main/skills`），可一键安装目录下所有子技能。
- 修复语言获取逻辑：前端优先（`__event_call__` + 超时保护），并回退到请求头与用户资料。

## 核心特性

- 原生技能管理
- 用户范围内的 list/show/install/create/update/delete
- 每步操作提供状态栏反馈

## 方法

- `list_skills`
- `show_skill`
- `install_skill`
- `create_skill`
- `update_skill`
- `delete_skill`

## 安装方式

1. 打开 OpenWebUI → Workspace → Tools
2. 在官方市场安装 **OpenWebUI Skills 管理工具**
3. 保存并在模型/聊天中启用

### 手动安装（备选）

- 新建 Tool 并粘贴：
   - `plugins/tools/openwebui-skills-manager/openwebui_skills_manager.py`
