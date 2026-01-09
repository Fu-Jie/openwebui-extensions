# 开源项目重组实施计划

## 1. 目标
将 `openwebui-extras` 打造为一个 **OpenWebUI 增强功能集合库**，专注于分享个人开发和收集的优质插件、提示词，而非作为一个独立的 Python 应用程序发布。

## 2. 当前状态分析
- **定位明确**：项目核心价值在于内容（Plugins, Prompts, Docs），而非运行环境。
- **结构已优化**：
    - `plugins/`：核心插件资源。
    - `prompts/`：提示词资源。
    - `docs/`：详细的使用和开发文档。
    - `scripts/`：辅助工具脚本（如本地测试用的 `run.py`）。
- **已移除不必要文件**：移除了 `requirements.txt`，避免用户误以为需要配置 Python 环境。

## 3. 重组方案

### 3.1 目录结构
保持当前的清晰结构，强调“拿来即用”：

```
openwebui-extras/
├── docs/                 # 文档与教程
├── plugins/              # 插件库 (核心资源)
│   ├── actions/
│   ├── filters/
│   ├── pipelines/
│   └── pipes/
├── prompts/              # 提示词库 (核心资源)
├── scripts/              # 维护者工具 (非用户必须)
├── LICENSE               # MIT 许可证
├── README.md             # 项目入口与资源索引
└── index.html            # 项目展示页
```

### 3.2 核心调整
1.  **移除依赖管理**：删除了 `requirements.txt`。用户不需要 `pip install` 任何东西，只需下载对应的 `.py` 或 `.md` 文件导入 OpenWebUI 即可。
2.  **文档侧重**：README 和文档将侧重于“如何下载”和“如何导入”，而不是“如何安装项目”。

### 3.3 后续建议
1.  **资源索引**：建议在 `README.md` 中维护一个高质量的插件/提示词索引表，方便用户快速查找。
2.  **贡献指南**：制定简单的 `CONTRIBUTING.md`，告诉其他人如何提交他们的插件或提示词（例如：只需提交文件到对应目录）。
3.  **版本控制**：虽然不需要 Python 环境，但建议在插件文件的头部注释中保留版本号和兼容性说明（如 `Compatible with OpenWebUI v0.3.x`）。

## 4. 发布流程
1.  **提交更改**：`git add . && git commit -m "Update project structure for resource sharing"`
2.  **推送到 GitHub**。
3.  **宣传**：在 OpenWebUI 社区分享此仓库链接。

---
*生成时间：2025-12-19*
