# Plugins（插件）

[English](./README.md) | 中文

这里是 OpenWebUI Extensions 的“仓库侧插件入口”。如果你想先高效发现适合自己的插件，建议先看 [插件中心](../docs/plugins/index.zh.md)；当你需要查看源码目录、本地 README 或 repo-only 条目时，再回到这里。

## 推荐浏览方式

1. 先用 [插件中心](../docs/plugins/index.zh.md) 看精选推荐和当前目录
2. 当你已经知道自己需要 Action / Filter / Pipe / Tool / Pipeline 时，再进入对应类型目录
3. 当你需要源码文件、本地 README 或 repo-only 说明时，再打开具体插件文件夹

## 按目标走入口

| 我想要... | 去这里 | 你会看到 |
| --- | --- | --- |
| 做可视化与交互输出 | [Actions](../docs/plugins/actions/index.zh.md) | 思维导图、信息图、闪记卡、精读与导出类插件 |
| 提升上下文与输出质量 | [Filters](../docs/plugins/filters/index.zh.md) | 压缩、格式清理、上下文注入、repo 感知辅助能力 |
| 搭建自主工作流 | [Pipes](../docs/plugins/pipes/index.zh.md) | 高级模型集成与更偏 Agent 风格的运行时能力 |
| 让工具跨模型复用 | [Tools](../docs/plugins/tools/index.zh.md) | Skills 管理、主动生成思维导图、批量安装辅助工具 |
| 从发现路径完整浏览全部 | [插件中心](../docs/plugins/index.zh.md) | 精选推荐、当前目录、repo-only 条目说明 |

## 插件类型

- [Actions](./actions/README_CN.md) — 负责按钮交互、导出、可视化和用户侧聊天体验
- [Filters](./filters/README_CN.md) — 负责消息链路中的上下文处理、格式清理与质量控制
- [Pipes](./pipes/README_CN.md) — 负责模型集成与高级工作流运行时
- [Tools](./tools/README_CN.md) — 负责跨模型复用的原生工具能力
- [Pipelines](../docs/plugins/pipelines/index.zh.md) — 负责编排型参考内容与历史实验项

## 仓库结构

```text
plugins/
├── actions/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
├── filters/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
├── pipes/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
├── tools/<plugin>/
│   ├── <plugin>.py
│   ├── README.md
│   └── README_CN.md
└── pipelines/<plugin>/
    └── ...
```

> **当前仓库规则：** 插件源码保持为**单个 Python 文件 + 内建 i18n**，不要再拆出单独的 `_cn.py` 源码文件。

## Repo-only 条目

有些条目会先在仓库中出现，文档镜像页稍后再补。目前比较典型的有：

- `plugins/pipes/iflow-sdk-pipe/`
- `plugins/filters/chat-session-mapping-filter/`

## 安装路径

1. **OpenWebUI Community** — 直接从 [Fu-Jie 的主页](https://openwebui.com/u/Fu-Jie) 安装
2. **文档页 + 仓库源码** — 先用文档选型，再上传对应 `.py` 文件
3. **本地批量安装** — 配置好 `.env` 后执行 `python scripts/install_all_plugins.py`
