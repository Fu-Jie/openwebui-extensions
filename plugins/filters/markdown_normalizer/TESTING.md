# Markdown Normalizer v1.1.0 - Comprehensive Testing Guide

This document describes the testing methodology and test coverage for Markdown Normalizer v1.1.0.

## Test Coverage

### 1. JSON String with Escape Sequences
**Purpose**: Verify that escape sequences in JSON strings are preserved inside code blocks.

**Input**:
```markdown
Here's a JSON example:
```json
{
  "message": "Line 1\nLine 2\nLine 3",
  "pattern": "\d+\t\w+",
  "path": "C:\\Users\\Documents\\file.txt"
}
```
Some text with\nescapes\nhere.
```

**Expected Behavior**:
- ✅ Escape sequences **inside** code block are **preserved**: `\n`, `\t`, `\\` remain unchanged
- ✅ Escape sequences **outside** code block are **converted**: `\n` → newline, `\t` → tab

**Validation**: JSON remains valid and parseable after normalization.

---

### 2. Python Regex Patterns
**Purpose**: Verify that regex patterns with special characters are preserved.

**Input**:
```markdown
Python regex example:
```python
pattern = r"\d+\s+\w+"
text = "Match this\nand this\ttoo"
```
Regular text\nwith\nescapes.
```

**Expected Behavior**:
- ✅ Regex patterns preserved: `\d+\s+\w+` remains unchanged
- ✅ String literals in code preserved: `\n` and `\t` remain as literals

---

### 3. Multiple Code Blocks
**Purpose**: Verify that multiple code blocks in the same document are handled correctly.

**Input**:
```markdown
First block:
```javascript
const msg = "Line 1\nLine 2";
```
Text with\nescape.
```python
msg = "Line 1\nLine 2"
```
More text\nhere.
```

**Expected Behavior**:
- ✅ All code blocks preserve escape sequences independently
- ✅ Text between code blocks has escapes converted

---

### 4. Fullwidth Symbols
**Purpose**: Verify that fullwidth quotation marks and other symbols are converted.

**Input**:
```markdown
Code with fullwidth:
```python
print(＂hello＂)
print(＇world＇)
value = （１，２，３）
```
```

**Expected Behavior** (when `enable_fullwidth_symbol_fix=True`):
- ✅ `＂` (U+FF02) → `"` (ASCII)
- ✅ `＇` (U+FF07) → `'` (ASCII)
- ✅ `（` → `(`, `）` → `)`
- ✅ `，` → `,`

**Output**:
```python
print("hello")
print('world')
value = (1,2,3)
```

---

### 5. Mixed Content (Code + LaTeX + Tables)
**Purpose**: Verify that different markdown elements are processed correctly together.

**Input**:
```markdown
# Heading
Here's a table:
| Column 1 | Column 2
| Value 1 | Value 2

Code block:
```json
{"key": "value\nwith\nescape"}
```

LaTeX: \[ E = mc^2 \]

More text\nwith\nescapes.
```

**Expected Behavior**:
- ✅ Code blocks: escapes preserved
- ✅ LaTeX: `\[` → `$$`, `\]` → `$$`
- ✅ Tables: missing `|` added at end
- ✅ Regular text: escapes converted

---

### 6. Edge Cases
**Purpose**: Verify robustness with edge cases.

**Test Cases**:
- Empty code blocks: ` ``` ``` `
- Inline code: `` `code\nhere` ``
- Consecutive code blocks
- Code blocks at start/end of document

**Expected Behavior**:
- ✅ No crashes or exceptions
- ✅ Graceful handling of malformed input

---

### 7. Thought Tags with Escapes
**Purpose**: Verify thought tag normalization works with escape sequences.

**Input**:
```markdown
<think>
Thinking about\nthis problem
</think>Result text\nhere.
```

**Expected Behavior**:
- ✅ `<think>` → `<thought>`
- ✅ `</think>` → `</thought>\n\n`
- ✅ Escapes outside tags converted

---

## Configuration Tested

### Safe Mode (Default)
```python
enable_escape_fix=True
enable_escape_fix_in_code_blocks=False  # Safe default
```

**Behavior**: Escape fixes only apply **outside** code blocks.

### Unsafe Mode (Opt-in)
```python
enable_escape_fix=True
enable_escape_fix_in_code_blocks=True  # Opt-in
```

**Behavior**: Escape fixes apply **everywhere** (original behavior, may break code).

---

## Test Results

All 7 comprehensive test cases **PASS** ✅

### Test Execution
```bash
cd plugins/filters/markdown_normalizer
python3 test_markdown_normalizer.py
```

**Output**:
```
Ran 15 tests in 0.002s
OK
```

---

## Validation Criteria

For a test to **PASS**, it must meet these criteria:

1. **No Exceptions**: Code runs without errors
2. **Code Preservation**: Escape sequences in code blocks remain unchanged
3. **Text Conversion**: Escape sequences outside code blocks are converted
4. **Feature Correctness**: Specific features (LaTeX, tables, etc.) work as documented
5. **Edge Case Handling**: No crashes on malformed input

---

## Known Limitations

1. **Inline Code**: Escape sequences in inline code (`` `code` ``) are **not** preserved (by design, as inline code is harder to detect reliably)
2. **Nested Code Blocks**: Theoretical edge case (not supported in standard Markdown)
3. **Code Blocks Without Language**: Handled but not specially processed

---

## Regression Prevention

To prevent regressions, always run the full test suite before releasing:

```bash
python3 test_markdown_normalizer.py -v
```

All tests must pass before merging changes.
