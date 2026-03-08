from plugins.filters.markdown_normalizer.markdown_normalizer import ContentNormalizer, NormalizerConfig

def test_error_rollback():
    """Issue 57-1: Ensure content is NOT modified if a cleaner raises an exception."""
    def broken_cleaner(text): raise RuntimeError("Plugin Crash Simulation")
    config = NormalizerConfig(custom_cleaners=[broken_cleaner])
    norm = ContentNormalizer(config)
    raw_text = "Content that should NOT be modified on error."
    res = norm.normalize(raw_text)
    assert res == raw_text

def test_inline_code_protection():
    """Issue 57-2: Protect backslashes inside inline code blocks."""
    norm = ContentNormalizer(NormalizerConfig(enable_escape_fix=True))
    inline_code = "Regex: `[\\\\n\\\\r]` and Path: `C:\\\\\\\\Windows` and Normal: \\\\n"
    res = norm.normalize(inline_code)
    # The normal \\\\n at the end SHOULD be converted to actual \n
    # The backslashes inside ` ` should NOT be converted.
    assert "`[\\\\n\\\\r]`" in res
    assert "`C:\\\\\\\\Windows`" in res
    assert "\n" in res

def test_code_block_escape_control():
    """Issue 57-3: Verify enable_escape_fix_in_code_blocks valve."""
    # input code: print('\\n')
    # representation: "print('\\\\n')"
    block_text = "```python\nprint('\\\\n')\n```"
    
    # Subcase A: Disabled (Default)
    norm_off = ContentNormalizer(NormalizerConfig(enable_escape_fix_in_code_blocks=False))
    assert norm_off.normalize(block_text) == block_text
    
    # Subcase B: Enabled
    norm_on = ContentNormalizer(NormalizerConfig(enable_escape_fix_in_code_blocks=True))
    # Expected: "```python\nprint('\n')\n```"
    res = norm_on.normalize(block_text)
    assert "\n" in res
    assert "\\n" not in res.split("```")[1]

def test_latex_protection():
    """Regression: Ensure LaTeX commands are not corrupted by escape fix."""
    norm = ContentNormalizer(NormalizerConfig(enable_escape_fix=True))
    latex_text = "Math: $\\\\times \\\\theta \\\\nu$ and Normal: \\\\n"
    res = norm.normalize(latex_text)
    assert "$\\\\times \\\\theta \\\\nu$" in res
    assert "\n" in res

if __name__ == "__main__":
    test_error_rollback()
    test_inline_code_protection()
    test_code_block_escape_control()
    test_latex_protection()
    print("All tests passed!")
