"""
Comprehensive Permission Control Test Suite
Tests all permission control scenarios for GitHub Copilot SDK
"""

import argparse
import asyncio
import logging
import re
from typing import Any, Dict, List, Tuple

from copilot import CopilotClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def build_permission_handler(allow_all: bool, allow_shell: bool, pattern: str):
    async def on_permission_request(request: Dict[str, Any], context: Dict[str, str]):
        kind = request.get("kind")
        # Shell requests use 'fullCommandText' not 'command'
        command = request.get("fullCommandText", "") or request.get("command", "")

        if allow_all:
            logger.info("✅ Approved (allow-all): kind=%s command=%r", kind, command)
            return {"kind": "approved"}

        if kind in ("read", "url"):
            logger.info("✅ Approved (safe): kind=%s", kind)
            return {"kind": "approved"}

        if kind == "shell":
            if allow_shell:
                logger.info("✅ Approved (allow-shell): command=%r", command)
                return {"kind": "approved"}

            if pattern and command:
                try:
                    if re.match(pattern, command):
                        logger.info(
                            "✅ Approved (regex match): pattern=%r command=%r",
                            pattern,
                            command,
                        )
                        return {"kind": "approved"}
                except re.error as exc:
                    logger.error("Invalid regex pattern: %s (%s)", pattern, exc)

        logger.warning("❌ Denied: kind=%s command=%r", kind, command)
        return {"kind": "denied-by-rules", "rules": [{"kind": "test-suite"}]}

    return on_permission_request


async def run_test(
    model: str, allow_all: bool, allow_shell: bool, pattern: str, prompt: str
) -> Tuple[bool, str]:
    """Run a single test and return (success, response)"""
    try:
        client = CopilotClient()
        await client.start()

        session = await client.create_session(
            {
                "model": model,
                "on_permission_request": build_permission_handler(
                    allow_all=allow_all,
                    allow_shell=allow_shell,
                    pattern=pattern,
                ),
            }
        )

        response = await session.send_and_wait({"prompt": prompt})
        await client.stop()

        content = response.data.content
        # Check if response indicates success or denial
        denied_keywords = [
            "不允许",
            "无法",
            "对不起",
            "Sorry",
            "can't",
            "cannot",
            "not have permission",
        ]
        is_denied = any(kw in content for kw in denied_keywords)

        return (not is_denied, content)
    except Exception as e:
        logger.error("Test failed with exception: %s", e)
        return (False, str(e))


async def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive permission control test suite."
    )
    parser.add_argument("--model", default="gpt-4.1", help="Model ID for testing.")

    args = parser.parse_args()

    # Test cases: (name, allow_all, allow_shell, pattern, prompt, expected_approved)
    test_cases = [
        ("Default Deny Shell", False, False, "", "请执行: ls -la", False),
        ("Allow All", True, False, "", "请执行: ls -la", True),
        ("Allow Shell", False, True, "", "请执行: pwd", True),
        ("Regex Match: ^ls", False, False, "^ls", "请执行: ls -la", True),
        ("Regex No Match: ^ls vs pwd", False, False, "^ls", "请执行: pwd", False),
        (
            "Regex Complex: ^(ls|pwd|echo)",
            False,
            False,
            "^(ls|pwd|echo)",
            "请执行: pwd",
            True,
        ),
        (
            "Regex Complex No Match: git",
            False,
            False,
            "^(ls|pwd|echo)",
            "请执行: git status",
            False,
        ),
        (
            "Read Permission (Always Allow)",
            False,
            False,
            "",
            "Read the file: README.md",
            True,
        ),
    ]

    results = []
    logger.info("=" * 80)
    logger.info("Starting Comprehensive Permission Control Test Suite")
    logger.info("Model: %s", args.model)
    logger.info("=" * 80)

    for i, (name, allow_all, allow_shell, pattern, prompt, expected) in enumerate(
        test_cases, 1
    ):
        logger.info("\n[Test %d/%d] %s", i, len(test_cases), name)
        logger.info(
            "  Config: allow_all=%s, allow_shell=%s, pattern=%r",
            allow_all,
            allow_shell,
            pattern,
        )
        logger.info("  Prompt: %s", prompt)

        approved, response = await run_test(
            args.model, allow_all, allow_shell, pattern, prompt
        )
        passed = approved == expected

        status = "✅ PASS" if passed else "❌ FAIL"
        results.append((name, passed))

        logger.info(
            "  Expected: %s, Got: %s - %s",
            "Approved" if expected else "Denied",
            "Approved" if approved else "Denied",
            status,
        )
        logger.info(
            "  Response: %s",
            response[:100] + "..." if len(response) > 100 else response,
        )

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for name, passed in results:
        logger.info("%s %s", "✅" if passed else "❌", name)

    logger.info("-" * 80)
    logger.info(
        "Total: %d/%d tests passed (%.1f%%)",
        passed_count,
        total_count,
        100 * passed_count / total_count,
    )

    if passed_count == total_count:
        logger.info("🎉 All tests passed!")
    else:
        logger.warning("⚠️  Some tests failed. Please review the logs.")


if __name__ == "__main__":
    asyncio.run(main())
