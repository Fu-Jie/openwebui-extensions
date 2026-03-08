#!/usr/bin/env python3
"""
Test script for auto-discovery and deduplication features.

Tests:
1. GitHub repo root URL detection
2. URL normalization for discovery
3. Duplicate URL removal in batch mode
"""

import re
from typing import List


def is_github_repo_root(url: str) -> bool:
    """Check if URL is a GitHub repo root (e.g., https://github.com/owner/repo)."""
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/?$", url)
    return match is not None


def normalize_github_repo_url(url: str) -> str:
    """Convert GitHub repo root URL to tree discovery URL (assuming main/master branch)."""
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/?$", url)
    if match:
        owner = match.group(1)
        repo = match.group(2)
        # Try main branch first, API will handle if it doesn't exist
        return f"https://github.com/{owner}/{repo}/tree/main"
    return url


def test_repo_root_detection():
    """Test GitHub repo root URL detection."""
    test_cases = [
        (
            "https://github.com/nicobailon/visual-explainer",
            True,
            "Repo root without trailing slash",
        ),
        (
            "https://github.com/nicobailon/visual-explainer/",
            True,
            "Repo root with trailing slash",
        ),
        ("https://github.com/nicobailon/visual-explainer/tree/main", False, "Tree URL"),
        (
            "https://github.com/nicobailon/visual-explainer/blob/main/README.md",
            False,
            "Blob URL",
        ),
        ("https://github.com/nicobailon", False, "Only owner"),
        (
            "https://raw.githubusercontent.com/nicobailon/visual-explainer/main/test.py",
            False,
            "Raw URL",
        ),
    ]

    print("=" * 70)
    print("Test 1: GitHub Repo Root URL Detection")
    print("=" * 70)

    passed = 0
    for url, expected, description in test_cases:
        result = is_github_repo_root(url)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1

        print(f"\n{status} | {description}")
        print(f"  URL: {url}")
        print(f"  Expected: {expected}, Got: {result}")

    print(f"\nTotal: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_url_normalization():
    """Test URL normalization for discovery."""
    test_cases = [
        (
            "https://github.com/nicobailon/visual-explainer",
            "https://github.com/nicobailon/visual-explainer/tree/main",
        ),
        (
            "https://github.com/nicobailon/visual-explainer/",
            "https://github.com/nicobailon/visual-explainer/tree/main",
        ),
        (
            "https://github.com/Fu-Jie/openwebui-extensions",
            "https://github.com/Fu-Jie/openwebui-extensions/tree/main",
        ),
        (
            "https://github.com/user/repo/tree/main",
            "https://github.com/user/repo/tree/main",
        ),  # No change for tree URLs
    ]

    print("\n" + "=" * 70)
    print("Test 2: URL Normalization for Auto-Discovery")
    print("=" * 70)

    passed = 0
    for url, expected in test_cases:
        result = normalize_github_repo_url(url)
        status = "✓ PASS" if result == expected else "✗ FAIL"
        if result == expected:
            passed += 1

        print(f"\n{status}")
        print(f"  Input:    {url}")
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")

    print(f"\nTotal: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


def test_duplicate_removal():
    """Test duplicate URL removal in batch mode."""
    test_cases = [
        {
            "name": "Single URL",
            "urls": ["https://github.com/o/r/tree/main/s1"],
            "unique": 1,
            "duplicates": 0,
        },
        {
            "name": "Duplicate URLs",
            "urls": [
                "https://github.com/o/r/tree/main/s1",
                "https://github.com/o/r/tree/main/s1",
                "https://github.com/o/r/tree/main/s2",
            ],
            "unique": 2,
            "duplicates": 1,
        },
        {
            "name": "Multiple duplicates",
            "urls": [
                "https://github.com/o/r/tree/main/s1",
                "https://github.com/o/r/tree/main/s1",
                "https://github.com/o/r/tree/main/s1",
                "https://github.com/o/r/tree/main/s2",
                "https://github.com/o/r/tree/main/s2",
            ],
            "unique": 2,
            "duplicates": 3,
        },
    ]

    print("\n" + "=" * 70)
    print("Test 3: Duplicate URL Removal")
    print("=" * 70)

    passed = 0
    for test_case in test_cases:
        urls = test_case["urls"]
        expected_unique = test_case["unique"]
        expected_duplicates = test_case["duplicates"]

        # Deduplication logic
        seen_urls = set()
        unique_urls = []
        duplicates_removed = 0
        for url_item in urls:
            url_str = str(url_item).strip()
            if url_str not in seen_urls:
                unique_urls.append(url_str)
                seen_urls.add(url_str)
            else:
                duplicates_removed += 1

        unique_match = len(unique_urls) == expected_unique
        dup_match = duplicates_removed == expected_duplicates
        test_pass = unique_match and dup_match

        status = "✓ PASS" if test_pass else "✗ FAIL"
        if test_pass:
            passed += 1

        print(f"\n{status} | {test_case['name']}")
        print(f"  Input URLs: {len(urls)}")
        print(f"  Unique: Expected {expected_unique}, Got {len(unique_urls)}")
        print(
            f"  Duplicates Removed: Expected {expected_duplicates}, Got {duplicates_removed}"
        )

    print(f"\nTotal: {passed}/{len(test_cases)} passed")
    return passed == len(test_cases)


if __name__ == "__main__":
    print("\n" + "🔹" * 35)
    print("Auto-Discovery & Deduplication Tests")
    print("🔹" * 35)

    results = [
        test_repo_root_detection(),
        test_url_normalization(),
        test_duplicate_removal(),
    ]

    print("\n" + "=" * 70)
    if all(results):
        print("✅ All tests passed!")
    else:
        print(f"⚠️ Some tests failed: {sum(results)}/3 test groups passed")
    print("=" * 70)
