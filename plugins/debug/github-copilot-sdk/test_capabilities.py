import asyncio
import os
import json
import sys
from copilot import CopilotClient, define_tool
from copilot.types import SessionConfig
from pydantic import BaseModel, Field


# Define a simple tool for testing
class RandomNumberParams(BaseModel):
    min: int = Field(description="Minimum value")
    max: int = Field(description="Maximum value")


@define_tool(description="Generate a random integer within a range.")
async def generate_random_number(params: RandomNumberParams) -> str:
    import random

    return f"Result: {random.randint(params.min, params.max)}"


async def main():
    print(f"Running tests with Python: {sys.executable}")

    # 1. Setup Client
    client = CopilotClient({"log_level": "error"})
    await client.start()

    try:
        print("\n=== Test 1: Session Creation & Formatting Injection ===")
        # Use gpt-4o or similar capable model
        model_id = "gpt-5-mini"

        system_message_config = {
            "mode": "append",
            "content": "You are a test assistant. Always start your response with 'TEST_PREFIX: '.",
        }

        session_config = SessionConfig(
            model=model_id,
            system_message=system_message_config,
            tools=[generate_random_number],
        )

        session = await client.create_session(config=session_config)
        session_id = session.session_id
        print(f"Session Created: {session_id}")

        # Test 1.1: Check system prompt effect
        resp = await session.send_and_wait(
            {"prompt": "Say hello.", "mode": "immediate"}
        )
        content = resp.data.content
        print(f"Response 1: {content}")

        if "TEST_PREFIX:" in content:
            print("✅ System prompt injection active.")
        else:
            print("⚠️ System prompt injection NOT detected.")

        print("\n=== Test 2: Tool Execution ===")
        # Test Tool Usage
        prompt_with_tool = (
            "Generate a random number between 100 and 200 using the tool."
        )
        print(f"Sending: {prompt_with_tool}")

        # We need to listen to events to verify tool execution,
        # but send_and_wait handles it internally and returns the final answer.
        # We check if the final answer mentions the result.

        resp_tool = await session.send_and_wait(
            {"prompt": prompt_with_tool, "mode": "immediate"}
        )
        tool_content = resp_tool.data.content
        print(f"Response 2: {tool_content}")

        if "Result:" in tool_content or any(char.isdigit() for char in tool_content):
            print("✅ Tool likely executed (numbers found).")
        else:
            print("⚠️ Tool execution uncertain.")

        print("\n=== Test 3: Context Retention (Memory) ===")
        # Store a fact
        await session.send_and_wait(
            {"prompt": "My secret code is 'BLUE-42'. Remember it.", "mode": "immediate"}
        )
        print("Fact sent.")

        # Retrieve it
        resp_mem = await session.send_and_wait(
            {"prompt": "What is my secret code?", "mode": "immediate"}
        )
        mem_content = resp_mem.data.content
        print(f"Response 3: {mem_content}")

        if "BLUE-42" in mem_content:
            print("✅ Context retention successful.")
        else:
            print("⚠️ Context retention failed.")

        # Cleanup
        await session.destroy()

        print("\n=== Test 4: Resume Session (Simulation) ===")
        # Note: Actual resuming depends on backend persistence.
        # The SDK's client.resume_session(id) tries to find it.
        # Since we destroyed it above, we expect failure or new session logic in real app.
        # But let's create a new one to persist, close client, and try to resume if process was same?
        # Actually persistence usually requires the Copilot Agent/Extension host to keep state or file backed.
        # The Python SDK defaults to file-based workspace in standard generic usage?
        # Let's just skip complex resume testing for this simple script as it depends on environment (vscode-chat-session vs file).
        print("Skipping complex resume test in script.")

    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        await client.stop()
        print("\nTests Completed.")


if __name__ == "__main__":
    asyncio.run(main())
