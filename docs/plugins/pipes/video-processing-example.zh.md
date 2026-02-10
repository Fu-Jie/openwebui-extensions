# 案例展示：视频高质量 GIF 转换与加速处理

本案例展示了如何使用 **GitHub Copilot SDK Pipe** 配合 **Minimax 2.1** 模型，通过底层工具（FFmpeg）对视频文件进行精细化处理：加速 1.4 倍并压缩至 20MB 以内的超高质量 GIF。

---

## 🎥 效果录屏

![视频处理过程演示](./video-processing-demo.gif)

> **场景描述**：用户上传了一个 38MB 的 `.mov` 录屏文件，要求加速 1.4 倍，并转换为 1280px 宽度、大小在 20MB 以内的高质量 GIF。模型自动分析了需求，编写并执行了双工作流 FFmpeg 指令。

---

## 🛠️ 技术实现

- **插件类型**: Pipe (GitHub Copilot SDK)
- **底层模型**: Minimax 2.1
- **核心能力**: 
    - **底层系统访问**: 自动检测并调用容器内的 `ffmpeg` 工具。
    - **双阶段优化 (Two-Pass Optimization)**:
        1. **阶段一**: 分析全视频帧生成 256 色最优调色板 (`palettegen`)。
        2. **阶段二**: 应用调色板进行高质量量化和抖动处理 (`paletteuse`)。
    - **参数精准控制**: 实现 1.4 倍 PTS 缩放、Lanczos 滤镜缩放及 20fps 帧率控制。

---

## 💬 对话实录

### 📥 导入对话记录
你可以下载原始对话数据并导入到你的 Open WebUI 中，查看模型如何一步步调试 FFmpeg 参数：
[:material-download: 下载原始对话 JSON](./video-processing-chat.json)

> **如何导入？**
> 在 Open WebUI 首页点击 **左侧侧边栏底部个人头像** -> **设置** -> **数据** -> **导入记录**，选择下载的文件即可。

### 1. 提交处理需求
**用户**指定了输入文件和详细参数：
- 加速：1.4x (setpts=PTS/1.4)
- 分辨率：宽度 1280px，等比例缩放
- 质量优化：必须使用调色板生成技术
- 约束：文件体积 < 20MB

### 2. 模型执行处理
**Minimax 2.1** 自动编写并执行了以下核心逻辑：
```bash
# 生成优化调色板
ffmpeg -i input.mov -vf "fps=20,scale=1280:-1:flags=lanczos,setpts=PTS/1.4,palettegen" palette.png
# 生成最终高质量 GIF
ffmpeg -i input.mov -i palette.png -lavfi "[0:v]fps=20,scale=1280:-1:flags=lanczos,setpts=PTS/1.4[v];[v][1:v]paletteuse" output.gif
```

### 3. 处理结果摘要
| 指标 | 原始视频 | 处理后 GIF | 状态 |
| :--- | :--- | :--- | :--- |
| **文件大小** | 38 MB | **14 MB** | ✅ 达标 |
| **分辨率** | 3024x1898 | 1280x803 | ✅ 缩放平滑 |
| **播放速度** | 1.0x | 1.4x | ✅ 节奏紧凑 |
| **色彩质量** | N/A | 256色最优量化 | ✨ 极其清晰 |

---

## 💡 为什么这个案例很有意义？

传统的 LLM 只能“告诉你”怎么做，而基于 **GitHub Copilot SDK** 的 Pipe 能够：
1. **理解** 复杂的多媒体处理参数。
2. **感知** 文件系统中的原始素材。
3. **执行** 耗时、耗能的二进制工具任务。
4. **验证** 产出物（体积、分辨率）是否符合用户的最终约束。

---

> [查看 GitHub Copilot SDK Pipe 源码](../../../plugins/pipes/github-copilot-sdk/README.md)
