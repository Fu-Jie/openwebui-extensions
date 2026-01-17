from markdown_normalizer import ContentNormalizer, NormalizerConfig


def test_side_effects():
    normalizer = ContentNormalizer(NormalizerConfig(enable_details_tag_fix=True))

    # Scenario 1: HTML code block
    code_block = """```html
<details>
  <summary>Click</summary>
  Content
</details>
```"""

    # Scenario 2: Python string
    python_code = """```python
html = "</details>"
print(html)
```"""

    print("--- Scenario 1: HTML Code Block ---")
    res1 = normalizer.normalize(code_block)
    print(repr(res1))
    if "</details>\n\n" in res1 and "```" in res1:
        print("WARNING: Modified inside HTML code block")

    print("\n--- Scenario 2: Python String ---")
    res2 = normalizer.normalize(python_code)
    print(repr(res2))
    if 'html = "</details>\n\n"' in res2:
        print("CRITICAL: Broke Python string literal")
    else:
        print("OK")


if __name__ == "__main__":
    test_side_effects()
