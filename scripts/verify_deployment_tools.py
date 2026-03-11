#!/usr/bin/env python3
"""
Quick verification script to ensure all deployment tools are in place.

This script checks that all necessary files for async_context_compression
local deployment are present and functional.
"""

import sys
from pathlib import Path


def main():
    """Check all deployment tools are ready."""
    base_dir = Path(__file__).parent.parent

    print("\n" + "=" * 80)
    print("✨ Async Context Compression Local Deployment Tools — Verification Status")
    print("=" * 80 + "\n")

    files_to_check = {
        "🐍 Python Scripts": [
            "scripts/deploy_async_context_compression.py",
            "scripts/deploy_filter.py",
            "scripts/deploy_pipe.py",
        ],
        "📖 Deployment Documentation": [
            "scripts/README.md",
            "scripts/QUICK_START.md",
            "scripts/DEPLOYMENT_GUIDE.md",
            "scripts/DEPLOYMENT_SUMMARY.md",
            "plugins/filters/async-context-compression/DEPLOYMENT_REFERENCE.md",
        ],
        "🧪 Test Files": [
            "tests/scripts/test_deploy_filter.py",
        ],
    }

    all_exist = True

    for category, files in files_to_check.items():
        print(f"\n{category}:")
        print("-" * 80)

        for file_path in files:
            full_path = base_dir / file_path
            exists = full_path.exists()
            status = "✅" if exists else "❌"

            print(f"  {status} {file_path}")

            if exists and file_path.endswith(".py"):
                size = full_path.stat().st_size
                lines = len(full_path.read_text().split("\n"))
                print(f"     └─ [{size} bytes, ~{lines} lines]")

            if not exists:
                all_exist = False

    print("\n" + "=" * 80)

    if all_exist:
        print("✅ All deployment tool files are ready!")
        print("=" * 80 + "\n")

        print("🚀 Quick Start (3 ways):\n")

        print("  Method 1: Easiest (Recommended)")
        print("  ─────────────────────────────────────────────────────────")
        print("    cd scripts")
        print("    python deploy_async_context_compression.py")
        print()

        print("  Method 2: Generic Tool")
        print("  ─────────────────────────────────────────────────────────")
        print("    cd scripts")
        print("    python deploy_filter.py")
        print()

        print("  Method 3: Deploy Other Filters")
        print("  ─────────────────────────────────────────────────────────")
        print("    cd scripts")
        print("    python deploy_filter.py --list")
        print("    python deploy_filter.py folder-memory")
        print()

        print("=" * 80 + "\n")
        print("📚 Documentation References:\n")
        print("  • Quick Start:        scripts/QUICK_START.md")
        print("  • Complete Guide:     scripts/DEPLOYMENT_GUIDE.md")
        print("  • Technical Summary:  scripts/DEPLOYMENT_SUMMARY.md")
        print("  • Script Info:        scripts/README.md")
        print("  • Test Coverage:      pytest tests/scripts/test_deploy_filter.py -v")
        print()

        print("=" * 80 + "\n")
        return 0
    else:
        print("❌ Some files are missing!")
        print("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
