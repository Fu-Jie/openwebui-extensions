#!/usr/bin/env python3
import os
import re
from pathlib import Path

plugin_dir = Path("plugins/pipes/github-copilot-sdk")
docs_dir = Path("docs/plugins/pipes")

new_ver = "0.12.0"
old_ver = "0.11.0"

# Updates definition
whats_new_cn = f"""## ✨ v{new_ver}：自适应动作面板、流排重拦截与全链路 TTFT 测定

- **📊 连续自适应看板 (Adaptive Actions Console)**：在 `.pipe_impl` 挂载了 `interactive_controls` 状态表，引导大模型按逻辑概率有选择性召回旧面板，实现不翻页连续持久化点击操作。
- **🛡️ 叠加流排重拦截 (Deduplicate Stream overlap)**：对接 `_dedupe_stream_chunk` 保守重叠裁剪，彻底消除二轮对话流重叠叠加异常。
- **⏱️ 分段 Profiling 埋点**：拆装本地预热阻断与云端网络 Trip 数据时间，直观测算 Time-to-First-Byte。
- **🧹 消除冗余解析**：剔除 Resume 过程对 MCP 的二次昂贵循环，提效握手微观时延。
"""

whats_new_en = f"""## ✨ v{new_ver}: Adaptive Actions Console, Stream Deduplication & Full TTFT Profiling

- **📊 Predictive Adaptive Console**: Introduced the `interactive_controls` state table inside local config workspace for the LLM to model continuous decision layouts that do not go stale.
- **🛡️ Stream Overlap Deduplication**: Mitigated overlay double delivery issues on `assistant.message_delta` using conservative overlap trimming logic during turn resumptions.
- **⏱️ Segmented Profiling Loadtimes**: Fine-grained timers identifying local startup overhead and pure cloud network turnaround time displayed directly in dev consoles.
- **🧹 Eliminate Redundancies**: Reduced redundant secondary heavy `_parse_mcp_servers()` loops inside session resumes for faster handshake callbacks.
"""

def update_whats_new(file_path, new_block, old_title_regex):
    if not file_path.exists():
        return
    content = file_path.read_text(encoding="utf-8")
    # Find the current What's New block.
    # We look for a line starting with `## ✨ v0.11.0` until the next delimiter or `---`
    pattern = rf"(## ✨ v?{re.escape(old_ver)}[\s\S]*?)(?=\n---|\n##)"
    if re.search(pattern, content):
        new_content = re.sub(pattern, new_block.strip() + "\n", content)
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Updated What's New in {file_path}")
    else:
        print(f"Could not find What's new block in {file_path}")

def global_replace_version(file_path):
    if not file_path.exists():
        return
    content = file_path.read_text(encoding="utf-8")
    new_content = content.replace(old_ver, new_ver)
    if content != new_content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Bumped version string in {file_path}")

# 1. Update What's New
update_whats_new(plugin_dir / "README_CN.md", whats_new_cn, f"v{old_ver}")
update_whats_new(plugin_dir / "README.md", whats_new_en, f"v{old_ver}")

# 2. Update Docs What's New
update_whats_new(docs_dir / "github-copilot-sdk.zh.md", whats_new_cn, f"v{old_ver}")
update_whats_new(docs_dir / "github-copilot-sdk.md", whats_new_en, f"v{old_ver}")

# 3. Global update everything else
files_to_bump = [
    plugin_dir / "README_CN.md",
    plugin_dir / "README.md",
    docs_dir / "github-copilot-sdk.zh.md",
    docs_dir / "github-copilot-sdk.md",
    docs_dir / "index.md",
    docs_dir / "index.zh.md",
    Path("README.md"),
    Path("README_CN.md"),
]

for f in files_to_bump:
    global_replace_version(f)

print("Updates complete! ✅")
