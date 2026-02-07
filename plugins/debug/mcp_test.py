import asyncio
import os
from copilot import CopilotClient


async def main():
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "Error: GH_TOKEN (or GITHUB_TOKEN) environment variable not set. Please export GH_TOKEN=... before running."
        )
        return

    client = CopilotClient()
    await client.start()

    async def on_permission_request(request, _ctx):
        if request.get("kind") == "mcp":
            return {"kind": "approved"}
        return {"kind": "approved"}

    session = await client.create_session(
        {
            "model": "gpt-5-mini",
            "mcp_servers": {
                "github": {
                    "type": "http",
                    "url": "https://api.githubcopilot.com/mcp/",
                    "headers": {"Authorization": f"Bearer {token}"},
                    "tools": ["*"],
                }
            }
        }
    )

    result = await session.send_and_wait(
        {
            "prompt": "Use GitHub MCP tools to find the owner of the 'awesome-openwebui' repository.",
        },timeout=1000
    )
    print(result.data.content)

    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())
