import sys
import os

# Add plugin dir to path
current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_dir = os.path.abspath(os.path.join(current_dir, "..", "filters", "markdown_normalizer"))
sys.path.append(plugin_dir)

from markdown_normalizer import ContentNormalizer, NormalizerConfig

def test_latex_protection():
    # Test case 1: The reported issue with \times
    content_1 = r"Calculation: $C(33, 6) \times C(16, 1)$"
    
    config = NormalizerConfig(enable_escape_fix=True)
    normalizer = ContentNormalizer(config)
    
    result_1 = normalizer.normalize(content_1)
    
    print("--- Test 1: \times Protection ---")
    print(f"Input:  {content_1}")
    print(f"Output: {result_1}")
    
    if r"\times" in result_1:
        print("✅ PASSED")
    else:
        print("❌ FAILED")

    # Test case 2: Other potential collisions like \nu (newline) or \theta (tab?)
    # Using raw strings carefully
    content_2 = r"Formula: $\theta = \nu + \tau$"
    result_2 = normalizer.normalize(content_2)
    
    print("\n--- Test 2: \theta and \nu Protection ---")
    print(f"Input:  {content_2}")
    print(f"Output: {result_2}")
    
    if r"\theta" in result_2 and r"\nu" in result_2:
        print("✅ PASSED")
    else:
        print("❌ FAILED")

if __name__ == "__main__":
    test_latex_protection()
