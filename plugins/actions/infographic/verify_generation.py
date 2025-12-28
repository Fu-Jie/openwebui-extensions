import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
import pathlib

# Load .env from the same directory as this script
env_path = pathlib.Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
# =================================================================
# Configuration
# =================================================================

API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to gpt-4o if not set

if not API_KEY or not BASE_URL:
    print(
        "Error: OPENAI_API_KEY and OPENAI_BASE_URL environment variables must be set."
    )
    sys.exit(1)

# =================================================================
# Prompts (Extracted from 信息图.py)
# =================================================================

SYSTEM_PROMPT_INFOGRAPHIC_ASSISTANT = """
You are a professional infographic design expert who can analyze user-provided text content and convert it into AntV Infographic syntax format.

## Infographic Syntax Specification

Infographic syntax is a Mermaid-like declarative syntax for describing infographic templates, data, and themes.

### Syntax Rules
- Entry uses `infographic <template-name>`
- Key-value pairs are separated by spaces, **absolutely NO colons allowed**
- Use two spaces for indentation
- Object arrays use `-` with line breaks

⚠️ **IMPORTANT WARNING: This is NOT YAML format!**
- ❌ Wrong: `children:` `items:` `data:` (with colons)
- ✅ Correct: `children` `items` `data` (without colons)

### Template Library & Selection Guide

#### 1. List & Hierarchy (Text-heavy)
-   **Linear & Short (Steps/Phases)** -> `list-row-horizontal-icon-arrow`
-   **Linear & Long (Rankings/Details)** -> `list-vertical`
-   **Grouped / Parallel (Features/Catalog)** -> `list-grid`
-   **Hierarchical (Org Chart/Taxonomy)** -> `tree-vertical` or `tree-horizontal`
-   **Central Idea (Brainstorming)** -> `mindmap`

#### 2. Sequence & Relationship (Flow-based)
-   **Time-based (History/Plan)** -> `sequence-roadmap-vertical-simple`
-   **Process Flow (Complex)** -> `sequence-zigzag` or `sequence-horizontal`
-   **Resource Flow / Distribution** -> `relation-sankey`
-   **Circular Relationship** -> `relation-circle`

#### 3. Comparison & Analysis
-   **Binary Comparison (A vs B)** -> `compare-binary`
-   **SWOT Analysis** -> `compare-swot`
-   **Multi-item Comparison Table** -> `compare-table`
-   **Quadrant Analysis (Importance vs Urgency)** -> `quadrant-quarter`

#### 4. Charts & Data (Metric-heavy)
-   **Key Metrics / Data Cards** -> `statistic-card`
-   **Distribution / Comparison** -> `chart-bar` or `chart-column`
-   **Trend over Time** -> `chart-line` or `chart-area`
-   **Proportion / Part-to-Whole** -> `chart-pie` or `chart-doughnut`

### Infographic Syntax Guide

#### 1. Structure
-   **Entry**: `infographic <template-name>`
-   **Blocks**: `data`, `theme`, `design` (optional)
-   **Format**: Key-value pairs separated by spaces, 2-space indentation.
-   **Arrays**: Object arrays use `-` (newline), simple arrays use inline values.

#### 2. Data Block (`data`)
-   `title`: Main title
-   `desc`: Subtitle or description
-   `items`: List of data items
-     - `label`: Item title
-     - `value`: Numerical value (required for Charts/Stats)
-     - `desc`: Item description (optional)
-     - `icon`: Icon name (e.g., `mdi/rocket-launch`)
-     - `time`: Time label (Optional, for Roadmap/Sequence)
-     - `children`: Nested items (ONLY for Tree/Mindmap/Sankey/SWOT)
-     - `illus`: Illustration name (ONLY for Quadrant)

#### 3. Theme Block (`theme`)
-   `colorPrimary`: Main color (Hex)
-   `colorBg`: Background color (Hex)
-   `palette`: Color list (Space separated)
-   `textColor`: Text color (Hex)
-   `stylize`: Style effect (e.g., `rough`, `flat`)

### Examples

#### Chart (Bar Chart)
infographic chart-bar
data
  title Revenue Growth
  desc Monthly revenue in 2024
  items
    - label Jan
      value 1200
    - label Feb
      value 1500
    - label Mar
      value 1800

#### Comparison (SWOT)
infographic compare-swot
data
  title Project SWOT
  items
    - label Strengths
      children
        - label Strong team
        - label Innovative tech
    - label Weaknesses
      children
        - label Limited budget
    - label Opportunities
      children
        - label Emerging market
    - label Threats
      children
        - label High competition

#### Relationship (Sankey)
infographic relation-sankey
data
  title Energy Flow
  items
    - label Solar
      value 100
      children
        - label Grid
          value 60
        - label Battery
          value 40
    - label Wind
      value 80
      children
        - label Grid
          value 80

#### Quadrant (Importance vs Urgency)
infographic quadrant-quarter
data
  title Task Management
  items
    - label Critical Bug
      desc Fix immediately
      illus mdi/bug
    - label Feature Request
      desc Plan for next sprint
      illus mdi/star

### Output Rules
1.  **Strict Syntax**: Follow the indentation and formatting rules exactly.
2.  **No Explanations**: Output ONLY the syntax code block.
3.  **Language**: Use the user's requested language for content.
"""

USER_PROMPT_GENERATE_INFOGRAPHIC = """
请分析以下文本内容，将其核心信息转换为 AntV Infographic 语法格式。

---
**用户上下文信息:**
用户姓名: {user_name}
当前日期时间: {current_date_time_str}
用户语言: {user_language}
---

**文本内容:**
{long_text_content}

请根据文本特点选择最合适的信息图模板，并输出规范的 infographic 语法。注意保持正确的缩进格式（两个空格）。
"""

# =================================================================
# Test Cases
# =================================================================

TEST_CASES = [
    {
        "name": "List Grid (Features)",
        "content": """
        MiniMax 2025 模型矩阵全解析：
        1. 极致 MoE 架构优化：国内首批 MoE 路线坚定者。
        2. Video-01 视频生成：杀手锏级多模态能力。
        3. 情感陪伴与角色扮演：源自星野基因。
        4. 超长上下文与精准召回：支持 128k+ 窗口。
        """,
    },
    {
        "name": "Tree Vertical (Hierarchy)",
        "content": """
        公司组织架构：
        - 研发部
            - 后端组
            - 前端组
        - 市场部
            - 销售组
            - 推广组
        """,
    },
    {
        "name": "Statistic Card (Metrics)",
        "content": """
        2024年Q4 核心指标：
        - 总用户数：1,234,567
        - 日活跃用户：89%
        - 营收增长：+45%
        """,
    },
    {
        "name": "Mindmap (Brainstorming)",
        "content": """
        人工智能的应用领域：
        - 生成式 AI：文本生成、图像生成、视频生成
        - 预测性 AI：股市预测、天气预报
        - 决策 AI：自动驾驶、游戏博弈
        """,
    },
    {
        "name": "SWOT Analysis",
        "content": """
        某初创咖啡品牌的 SWOT 分析：
        优势：产品口味独特，选址精准。
        劣势：品牌知名度低，资金压力大。
        机会：线上外卖市场增长，年轻人对精品咖啡需求增加。
        威胁：行业巨头价格战，原材料成本上涨。
        """,
    },
    {
        "name": "Sankey (Relationship)",
        "content": """
        家庭月度开支流向：
        总收入 10000 元。
        其中 4000 元用于房贷。
        3000 元用于日常消费（包括 2000 元餐饮，1000 元交通）。
        2000 元用于教育培训。
        1000 元存入银行。
        """,
    },
    {
        "name": "Quadrant (Analysis)",
        "content": """
        个人任务象限分析：
        - 紧急且重要：修复线上紧急 Bug，准备下午的客户会议。
        - 重要不紧急：制定年度学习计划，健身锻炼。
        - 紧急不重要：回复琐碎的邮件，接听推销电话。
        - 不紧急不重要：刷社交媒体，看无聊的综艺。
        """,
    },
    {
        "name": "Chart Bar (Data)",
        "content": """
        2023年各季度营收情况（亿元）：
        第一季度：12.5
        第二季度：15.8
        第三季度：14.2
        第四季度：18.9
        """,
    },
]

# =================================================================
# Helper Functions
# =================================================================


def generate_infographic(content):
    now = datetime.now()
    current_date_time_str = now.strftime("%Y年%m月%d日 %H:%M:%S")

    formatted_user_prompt = USER_PROMPT_GENERATE_INFOGRAPHIC.format(
        user_name="TestUser",
        current_date_time_str=current_date_time_str,
        user_language="zh-CN",
        long_text_content=content,
    )

    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_INFOGRAPHIC_ASSISTANT},
            {"role": "user", "content": formatted_user_prompt},
        ],
        "stream": False,
    }

    try:
        response = requests.post(
            f"{BASE_URL}/chat/completions", headers=headers, json=payload
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"API Request Failed: {e}")
        return None


def validate_syntax(syntax):
    if not syntax:
        return False, "Empty output"

    # Basic checks
    if "infographic" not in syntax.lower():
        return False, "Missing 'infographic' keyword"

    if "data" not in syntax.lower() and "items" not in syntax.lower():
        return False, "Missing 'data' or 'items' block"

    # Check for colons in keys (simple heuristic)
    lines = syntax.split("\n")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Ignore lines that are likely values or descriptions containing colons
        first_word = stripped.split()[0]
        if first_word in ["title", "desc", "label", "value", "time", "icon"]:
            continue  # These can have colons in value

        # Check for key: pattern at start of line
        if re.match(r"^\w+:", stripped):
            return False, f"Found colon in key: {stripped}"

    return True, "Syntax looks valid"


# =================================================================
# Main Execution
# =================================================================

import re


def main():
    print(f"Starting Infographic Generation Verification...")
    print(f"API: {BASE_URL}")
    print(f"Model: {MODEL}")
    print("-" * 50)

    results = []

    for case in TEST_CASES:
        print(f"\nTesting Case: {case['name']}")
        print("Generating...")

        output = generate_infographic(case["content"])

        if output:
            # Clean output (remove markdown code blocks if present)
            clean_output = output
            if "```" in output:
                match = re.search(
                    r"```(?:infographic|mermaid)?\s*(.*?)\s*```", output, re.DOTALL
                )
                if match:
                    clean_output = match.group(1).strip()

            print(f"Output Preview:\n{clean_output[:200]}...")

            is_valid, message = validate_syntax(clean_output)
            if is_valid:
                print(f"✅ Validation Passed: {message}")
                results.append({"name": case["name"], "status": "PASS"})
            else:
                print(f"❌ Validation Failed: {message}")
                print(f"Full Output:\n{output}")
                results.append({"name": case["name"], "status": "FAIL"})
        else:
            print("❌ Generation Failed")
            results.append({"name": case["name"], "status": "ERROR"})

    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    for res in results:
        print(f"{res['name']}: {res['status']}")


if __name__ == "__main__":
    main()
