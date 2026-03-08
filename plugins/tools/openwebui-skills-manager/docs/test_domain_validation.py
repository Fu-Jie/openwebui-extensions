#!/usr/bin/env python3
"""
Domain Whitelist Validation Test Script

This script demonstrates and tests the domain whitelist validation logic
used in OpenWebUI Skills Manager Tool.
"""

import urllib.parse
from typing import Tuple


def validate_domain_whitelist(url: str, trusted_domains: str) -> Tuple[bool, str]:
    """
    Validate if a URL's domain is in the trusted domains whitelist.

    Args:
        url: The URL to validate
        trusted_domains: Comma-separated list of trusted primary domains

    Returns:
        Tuple of (is_valid, reason)
    """
    try:
        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname or parsed.netloc

        if not hostname:
            return False, "No hostname found in URL"

        # Check scheme
        if parsed.scheme not in ("http", "https"):
            return (
                False,
                f"Unsupported scheme: {parsed.scheme} (only http/https allowed)",
            )

        # Parse trusted domains
        trusted_list = [
            d.strip().lower() for d in (trusted_domains or "").split(",") if d.strip()
        ]

        if not trusted_list:
            return False, "No trusted domains configured"

        hostname_lower = hostname.lower()

        # Check exact match or subdomain match
        for trusted_domain in trusted_list:
            # Exact match
            if hostname_lower == trusted_domain:
                return True, f"✓ Exact match: {hostname_lower} == {trusted_domain}"

            # Subdomain match
            if hostname_lower.endswith("." + trusted_domain):
                return (
                    True,
                    f"✓ Subdomain match: {hostname_lower}.endswith('.{trusted_domain}')",
                )

        # Not trusted
        reason = f"✗ Not in whitelist: {hostname} not matched by {trusted_list}"
        return False, reason

    except Exception as e:
        return False, f"Validation error: {e}"


def print_test_result(test_name: str, url: str, trusted_domains: str, expected: bool):
    """Pretty print a test result."""
    is_valid, reason = validate_domain_whitelist(url, trusted_domains)
    status = "✓ PASS" if is_valid == expected else "✗ FAIL"

    print(f"\n{status} | {test_name}")
    print(f"  URL: {url}")
    print(f"  Domains: {trusted_domains}")
    print(f"  Result: {reason}")


# Test Cases
if __name__ == "__main__":
    print("=" * 70)
    print("Domain Whitelist Validation Tests")
    print("=" * 70)

    # ========== Scenario 1: GitHub Only ==========
    print("\n" + "🔹" * 35)
    print("Scenario 1: GitHub Domain Only")
    print("🔹" * 35)

    github_domains = "github.com"

    print_test_result(
        "GitHub exact domain",
        "https://github.com/Fu-Jie/openwebui-extensions",
        github_domains,
        expected=True,
    )

    print_test_result(
        "GitHub API subdomain",
        "https://api.github.com/repos/Fu-Jie/openwebui-extensions",
        github_domains,
        expected=True,
    )

    print_test_result(
        "GitHub Gist subdomain",
        "https://gist.github.com/Fu-Jie/test",
        github_domains,
        expected=True,
    )

    print_test_result(
        "GitHub Raw (wrong domain)",
        "https://raw.githubusercontent.com/Fu-Jie/openwebui-extensions/main/test.py",
        github_domains,
        expected=False,
    )

    # ========== Scenario 2: GitHub + GitHub Raw ==========
    print("\n" + "🔹" * 35)
    print("Scenario 2: GitHub + GitHub Raw Content")
    print("🔹" * 35)

    github_all_domains = "github.com,githubusercontent.com"

    print_test_result(
        "GitHub Raw (now allowed)",
        "https://raw.githubusercontent.com/Fu-Jie/openwebui-extensions/main/test.py",
        github_all_domains,
        expected=True,
    )

    print_test_result(
        "GitHub Raw with subdomain",
        "https://cdn.jsdelivr.net/gh/Fu-Jie/openwebui-extensions/test.py",
        github_all_domains,
        expected=False,
    )

    # ========== Scenario 3: Multiple Trusted Domains ==========
    print("\n" + "🔹" * 35)
    print("Scenario 3: Multiple Trusted Domains")
    print("🔹" * 35)

    multi_domains = "github.com,huggingface.co,anthropic.com"

    print_test_result(
        "GitHub domain", "https://github.com/Fu-Jie/test", multi_domains, expected=True
    )

    print_test_result(
        "HuggingFace domain",
        "https://huggingface.co/models/gpt-4",
        multi_domains,
        expected=True,
    )

    print_test_result(
        "HuggingFace Hub subdomain",
        "https://hub.huggingface.co/models/gpt-4",
        multi_domains,
        expected=True,
    )

    print_test_result(
        "Anthropic domain",
        "https://anthropic.com/research",
        multi_domains,
        expected=True,
    )

    print_test_result(
        "Untrusted domain",
        "https://bitbucket.org/Fu-Jie/test",
        multi_domains,
        expected=False,
    )

    # ========== Edge Cases ==========
    print("\n" + "🔹" * 35)
    print("Edge Cases")
    print("🔹" * 35)

    print_test_result(
        "FTP scheme (not allowed)",
        "ftp://github.com/Fu-Jie/test",
        github_domains,
        expected=False,
    )

    print_test_result(
        "File scheme (not allowed)",
        "file:///etc/passwd",
        github_domains,
        expected=False,
    )

    print_test_result(
        "Case insensitive domain",
        "HTTPS://GITHUB.COM/Fu-Jie/test",
        github_domains,
        expected=True,
    )

    print_test_result(
        "Deep subdomain",
        "https://api.v2.github.com/repos",
        github_domains,
        expected=True,
    )

    print("\n" + "=" * 70)
    print("✓ All tests completed!")
    print("=" * 70)
