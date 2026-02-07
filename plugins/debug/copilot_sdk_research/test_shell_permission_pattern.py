import argparse
import asyncio
import logging
import re
from typing import Any, Dict

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
        logger.info("permission.request FULL: %s", request)
        logger.info("permission.request kind=%s command=%r", kind, command)

        if allow_all:
            return {"kind": "approved"}

        if kind in ("read", "url"):
            return {"kind": "approved"}

        if kind == "shell":
            if allow_shell:
                return {"kind": "approved"}

            if pattern and command:
                try:
                    if re.match(pattern, command):
                        return {"kind": "approved"}
                except re.error as exc:
                    logger.error("Invalid regex pattern: %s (%s)", pattern, exc)

        return {"kind": "denied-by-rules", "rules": [{"kind": "debug-shell-pattern"}]}

    return on_permission_request


async def main():
    parser = argparse.ArgumentParser(
        description="Test shell permission regex with GitHub Copilot SDK."
    )
    parser.add_argument(
        "--pattern", default="", help="Regex pattern for auto-approving shell commands."
    )
    parser.add_argument(
        "--allow-shell", action="store_true", help="Auto-approve all shell commands."
    )
    parser.add_argument(
        "--allow-all", action="store_true", help="Auto-approve all permission requests."
    )
    parser.add_argument(
        "--prompt",
        default="请执行: ls -la",
        help="Prompt to trigger a shell tool request.",
    )
    parser.add_argument("--model", default="gpt-5-mini", help="Model ID for testing.")

    args = parser.parse_args()

    client = CopilotClient()
    await client.start()

    session = await client.create_session(
        {
            "model": args.model,
            "on_permission_request": build_permission_handler(
                allow_all=args.allow_all,
                allow_shell=args.allow_shell,
                pattern=args.pattern,
            ),
        }
    )

    logger.info("Sending prompt: %s", args.prompt)
    response = await session.send_and_wait({"prompt": args.prompt})
    logger.info("Response: %s", response.data.content)

    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
