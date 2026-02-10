# Case Study: High-Quality Video to GIF Conversion

This case study demonstrates how to use the **GitHub Copilot SDK Pipe** with **Minimax 2.1** to perform professional-grade video processing: accelerating a video by 1.4x and converting it into a high-quality GIF under 20MB.

---

## 🎥 Recording

![Video Processing Demo](./video-processing-demo.gif)

> **Scenario**: The user uploaded a 38MB `.mov` recording and requested a 1.4x speed increase, 1280px width, and a file size limit of 20MB. The model automatically formulated, executed, and verified a two-pass FFmpeg workflow.

---

## 🛠️ Implementation

- **Plugin Type**: Pipe (GitHub Copilot SDK)
- **Base Model**: Minimax 2.1
- **Key Capabilities**: 
    - **System Tool Access**: Automatically detects and invokes `ffmpeg` within the container.
    - **Two-Pass Optimization**:
        1. **Pass 1**: Analyzes all frames to generate a custom 256-color palette (`palettegen`).
        2. **Pass 2**: Applies the palette for superior quantization and dithering (`paletteuse`).
    - **Precision Parameters**: Implements 1.4x PTS scaling, Lanczos scaling, and 20fps rate control.

---

## 💬 Conversation Highlights

### 📥 Import Conversation
You can download the raw chat data and import it into your Open WebUI to see how the model debugs and optimizes the FFmpeg parameters:
[:material-download: Download Chat JSON](./video-processing-chat.json)

> **How to Import?**
> In Open WebUI, click your **User Avatar** (bottom of left sidebar) -> **Settings** -> **Data** -> **Import Chats**, then select the downloaded file.

### 1. Processing Requirements
The **User** provided an input file and specific parameters:
- Speed: 1.4x (setpts=PTS/1.4)
- Resolution: 1280px width, auto height
- Optimization: Must use palette generation technology
- Constraint: File size < 20MB

### 2. Analysis Execution
**Minimax 2.1** generated and executed the following core logic:
```bash
# Pass 1: Generate optimal palette
ffmpeg -i input.mov -vf "fps=20,scale=1280:-1:flags=lanczos,setpts=PTS/1.4,palettegen" palette.png
# Pass 2: Generate final high-quality GIF
ffmpeg -i input.mov -i palette.png -lavfi "[0:v]fps=20,scale=1280:-1:flags=lanczos,setpts=PTS/1.4[v];[v][1:v]paletteuse" output.gif
```

### 3. Result Summary
| Metric | Original Video | Processed GIF | Status |
| :--- | :--- | :--- | :--- |
| **File Size** | 38 MB | **14 MB** | ✅ Success |
| **Resolution** | 3024x1898 | 1280x803 | ✅ Smooth |
| **Speed** | 1.0x | 1.4x | ✅ Accurate |
| **Color Quality** | N/A | Optimal 256-color | ✨ Crystal Clear |

---

## 💡 Why This Case Matters

Standard LLMs can only "tell you" how to use FFmpeg. However, a Pipe powered by the **GitHub Copilot SDK** can:
1. **Interpret** complex multimedia processing parameters.
2. **Access** raw files within the filesystem.
3. **Execute** resource-intensive binary tool tasks.
4. **Validate** that the output (size, resolution) meets the user's hard constraints.

---

> [View GitHub Copilot SDK Pipe Source Code](../../../plugins/pipes/github-copilot-sdk/README.md)
