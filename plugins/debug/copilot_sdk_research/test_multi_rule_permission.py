"""
Test multi-rule permission control pattern (VSCode-style)
Tests ordered rule matching like VSCode's chat.tools.terminal.autoApprove
SAFE VERSION: Uses harmless commands (echo/ls) only. No rm, no git.
"""

import argparse
import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Tuple

from copilot import CopilotClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def build_multi_rule_handler(rules_json: str):
    """
    Build permission handler with ordered rules (VSCode-style)
    """
    try:
        rules = json.loads(rules_json) if rules_json else {}
    except json.JSONDecodeError as e:
        logger.error("Invalid rules JSON: %s", e)
        rules = {}

    async def on_permission_request(request: Dict[str, Any], context: Dict[str, str]):
        kind = request.get("kind")
        command = request.get("fullCommandText", "") or request.get("command", "")

        # Always approve read and url
        if kind in ("read", "url"):
            return {"kind": "approved"}

        # For shell commands, apply ordered rules
        if kind == "shell" and command:
            for pattern, approved in rules.items():
                try:
                    if re.match(pattern, command):
                        if approved:
                            logger.info(
                                "✅ Approved (rule match): pattern=%r command=%r",
                                pattern,
                                command,
                            )
                            return {"kind": "approved"}
                        else:
                            logger.warning(
                                "❌ Denied (rule match): pattern=%r command=%r",
                                pattern,
                                command,
                            )
                            return {
                                "kind": "denied-by-rules",
                                "rules": [
                                    {"kind": "multi-rule-deny", "pattern": pattern}
                                ],
                            }
                except re.error as exc:
                    logger.error("Invalid pattern %r: %s", pattern, exc)
                    continue

        # Default deny for shell without matching rule
        logger.warning("❌ Denied (no matching rule): command=%r", command)
        return {"kind": "denied-by-rules", "rules": [{"kind": "no-rule-match"}]}

    return on_permission_request


async def run_test(model: str, rules_json: str, prompt: str) -> Tuple[bool, str]:
    """Run a single test and return (approved, response)"""
    try:
        client = CopilotClient()
        await client.start()

        session = await client.create_session(
            {
                "model": model,
                "on_permission_request": build_multi_rule_handler(rules_json),
            }
        )

        # Set a short timeout
        try:
            response = await asyncio.wait_for(
                session.send_and_wait({"prompt": prompt}), timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.error("Test Timed Out")
            return (False, "Timeout")
        finally:
            await client.stop()

        content = response.data.content
        # Heuristics to detect denial in response
        denied_keywords = [
            "不允许",
            "无法",
            "对不起",
            "Sorry",
            "can't",
            "cannot",
            "not have permission",
            "denied",
        ]
        is_denied = any(kw in content for kw in denied_keywords)

        return (not is_denied, content)
    except Exception as e:
        logger.error("Test failed: %s", e)
        return (False, str(e))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-4.1", help="Model ID")
    args = parser.parse_args()

    # LOGIC TEST RULES
    # 1. Deny "echo secret" explicitly (Specific Deny)
    # 2. Allow "echo" anything else (General Allow)
    # 3. Allow "ls" (General Allow)
    # 4. Deny everything else (Default Deny)
    logic_test_rules = {
        "^echo\\s+secret": False,  # Higher priority: Deny specific echo
        "^echo": True,  # Lower priority: Allow general echo
        "^ls": True,  # Allow ls
        ".*": False,  # Deny everything else (e.g. whoami)
    }

    rules_json = json.dumps(logic_test_rules)

    test_cases = [
        # 1. Matches Rule 2 (^echo) -> Should be Approved
        ("Allowed: Normal Echo", "请执行: echo 'hello world'", True),
        # 2. Matches Rule 3 (^ls) -> Should be Approved
        ("Allowed: LS", "请执行: ls -la", True),
        # 3. Matches Rule 1 (^echo\s+secret) -> Should be DENIED
        # This proves the ORDER matters. If it matched Rule 2 first, it would be allowed.
        ("Denied: Restricted Echo", "请执行: echo secret data", False),
        # 4. Matches Rule 4 (.*) -> Should be DENIED
        ("Denied: Unknown Command", "请执行: whoami", False),
    ]

    logger.info("=" * 80)
    logger.info("Safe Multi-Rule Logic Test (Proving Precedence)")
    logger.info("Rules: %s", json.dumps(logic_test_rules, indent=2))
    logger.info("=" * 80)

    results = []
    for i, (name, prompt, expected) in enumerate(test_cases, 1):
        logger.info("\n[Test %d/%d] %s", i, len(test_cases), name)
        logger.info("  Prompt: %s", prompt)

        approved, response = await run_test(args.model, rules_json, prompt)
        passed = approved == expected

        status = "✅ PASS" if passed else "❌ FAIL"
        results.append((name, passed))

        logger.info(
            "  Expected: %s, Got: %s - %s",
            "Approved" if expected else "Denied",
            "Approved" if approved else "Denied",
            status,
        )
        logger.info("  Response: %s", response[:100].replace("\n", " "))

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    passed_count = sum(1 for _, passed in results if passed)
    for name, passed in results:
        logger.info("%s %s", "✅" if passed else "❌", name)
    logger.info("Total: %d/%d tests passed", passed_count, len(results))


if __name__ == "__main__":
    asyncio.run(main())
