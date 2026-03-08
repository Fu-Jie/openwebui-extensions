from plugins.filters.markdown_normalizer.markdown_normalizer import ContentNormalizer, NormalizerConfig

def test_latex_display_math_protection():
    """Verify that $$\nabla$$ is NOT broken by escape fix."""
    config = NormalizerConfig(enable_escape_fix=True)
    norm = ContentNormalizer(config)
    
    # Input has literal backslash + n (represented as \\n in python code)
    # Total input: $$ \ n a b l a $$
    text = r"$$\nabla$$"
    res = norm.normalize(text)
    
    # It should NOT change literal \n to a newline inside $$
    assert "\n" not in res, f"LaTeX display math was corrupted with a real newline: {repr(res)}"
    assert res == text, f"Expected {repr(text)}, got {repr(res)}"

if __name__ == "__main__":
    try:
        test_latex_display_math_protection()
        print("✅ LaTeX protection test passed.")
    except AssertionError as e:
        print(f"❌ LaTeX protection test FAILED: {e}")
