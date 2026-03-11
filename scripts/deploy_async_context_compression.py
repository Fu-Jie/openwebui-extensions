#!/usr/bin/env python3
"""
Deploy Async Context Compression Filter Plugin

Fast deployment script specifically for async_context_compression Filter plugin.
This is a shortcut for: python deploy_filter.py async-context-compression

Usage:
    python deploy_async_context_compression.py

To get started:
    1. Create .env file with your OpenWebUI API key:
       echo "api_key=sk-your-key-here" > .env

    2. Make sure OpenWebUI is running on localhost:3000

    3. Run this script:
       python deploy_async_context_compression.py
"""

import sys
from pathlib import Path

# Import the generic filter deployment function
SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from deploy_filter import deploy_filter


def main():
    """Deploy async_context_compression filter to local OpenWebUI."""
    print("=" * 70)
    print("🚀 Deploying Async Context Compression Filter Plugin")
    print("=" * 70)
    print()

    # Deploy the filter
    success = deploy_filter("async-context-compression")

    if success:
        print()
        print("=" * 70)
        print("✅ Deployment successful!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Open OpenWebUI in your browser: http://localhost:3000")
        print("  2. Go to Settings → Filters")
        print("  3. Enable 'Async Context Compression'")
        print("  4. Configure Valves as needed")
        print("  5. Start using the filter in conversations")
        print()
    else:
        print()
        print("=" * 70)
        print("❌ Deployment failed!")
        print("=" * 70)
        print()
        print("Troubleshooting:")
        print("  • Check that OpenWebUI is running: http://localhost:3000")
        print("  • Verify API key in .env file")
        print("  • Check network connectivity")
        print()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
