# Mermaid Syntax Standards & Best Practices

This document summarizes the official syntax standards for Mermaid flowcharts, focusing on node labels, quoting rules, and special character handling. It serves as a reference for the `markdown_normalizer` plugin logic.

## 1. Node Shapes & Syntax

Mermaid supports various node shapes defined by specific wrapping characters.

| Shape | Syntax | Example |
| :--- | :--- | :--- |
| **Rectangle** (Default) | `id[Label]` | `A[Start]` |
| **Rounded** | `id(Label)` | `B(Process)` |
| **Stadium** (Pill) | `id([Label])` | `C([End])` |
| **Subroutine** | `id[[Label]]` | `D[[Subroutine]]` |
| **Cylinder** (Database) | `id[(Label)]` | `E[(Database)]` |
| **Circle** | `id((Label))` | `F((Point))` |
| **Double Circle** | `id(((Label)))` | `G(((Endpoint)))` |
| **Asymmetric** | `id>Label]` | `H>Flag]` |
| **Rhombus** (Decision) | `id{Label}` | `I{Decision}` |
| **Hexagon** | `id{{Label}}` | `J{{Prepare}}` |
| **Parallelogram** | `id[/Label/]` | `K[/Input/]` |
| **Parallelogram Alt** | `id[\Label\]` | `L[\Output\]` |
| **Trapezoid** | `id[/Label\]` | `M[/Trap/]` |
| **Trapezoid Alt** | `id[\Label/]` | `N[\TrapAlt/]` |

## 2. Quoting Rules (Critical)

### Why Quote?
Quoting node labels is **highly recommended** and sometimes **mandatory** to prevent syntax errors.

### Mandatory Quoting Scenarios
You **MUST** enclose labels in double quotes `"` if they contain:
1.  **Special Characters**: `()`, `[]`, `{}`, `;`, `"`, etc.
2.  **Keywords**: Words like `end`, `subgraph`, etc., if used in specific contexts.
3.  **Unicode/Emoji**: While often supported without quotes, quoting ensures consistent rendering across different environments.
4.  **Markdown**: If you want to use Markdown formatting (bold, italic) inside a label.

### Best Practice: Always Quote
To ensure robustness, especially when processing LLM-generated content which may contain unpredictable characters, **always enclosing labels in double quotes is the safest strategy**.

**Examples:**
*   ❌ Risky: `id(Start: 15:00)` (Colon might be interpreted as style separator)
*   ✅ Safe: `id("Start: 15:00")`
*   ❌ Broken: `id(Func(x))` (Nested parentheses break parsing)
*   ✅ Safe: `id("Func(x)")`

## 3. Escape Characters

Inside a quoted string:
*   Double quotes `"` must be escaped as `\"`.
*   HTML entities (e.g., `#35;` for `#`) can be used.

## 4. Plugin Logic Verification

The `markdown_normalizer` plugin implements the following logic:

1.  **Detection**: Identifies Mermaid node definitions using a comprehensive regex covering all shapes above.
2.  **Normalization**:
    *   Checks if the label is already quoted.
    *   If **NOT quoted**, it wraps the label in double quotes `""`.
    *   Escapes any existing double quotes inside the label (`"` -> `\"`).
3.  **Shape Preservation**: The regex captures the specific opening and closing delimiters (e.g., `((` and `))`) to ensure the node shape is strictly preserved during normalization.

**Conclusion**: The plugin's behavior of automatically adding quotes to unquoted labels is **fully aligned with Mermaid's official best practices** for robustness and error prevention.
