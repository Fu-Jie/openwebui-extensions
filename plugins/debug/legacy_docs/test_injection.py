import asyncio
import os
import sys
import json
from copilot import CopilotClient
from copilot.types import SessionConfig

# Define the formatting instruction exactly as in the plugin
FORMATTING_INSTRUCTION = (
    "\n\n[Formatting Guidelines]\n"
    "When providing explanations or descriptions:\n"
    "- Use clear paragraph breaks (double line breaks)\n"
    "- Break long sentences into multiple shorter ones\n"
    "- Use bullet points or numbered lists for multiple items\n"
    "- Add headings (##, ###) for major sections\n"
    "- Ensure proper spacing between different topics"
)


async def main():
    print(f"Python executable: {sys.executable}")

    # Check for GH_TOKEN
    token = os.environ.get("GH_TOKEN")
    if token:
        print("GH_TOKEN is set.")
    else:
        print(
            "Warning: GH_TOKEN not found in environment variables. Relying on CLI auth."
        )

    client_config = {"log_level": "debug"}

    client = CopilotClient(client_config)

    try:
        print("Starting client...")
        await client.start()

        # Test 1: Check available models
        try:
            models = await client.list_models()
            print(f"Connection successful. Found {len(models)} models.")
            model_id = "gpt-5-mini"  # User requested model
        except Exception as e:
            print(f"Failed to list models: {e}")
            return

        print(f"\nCreating session with model {model_id} and system injection...")

        system_message_config = {
            "mode": "append",
            "content": "You are a helpful assistant." + FORMATTING_INSTRUCTION,
        }

        session_config = SessionConfig(
            model=model_id, system_message=system_message_config
        )

        session = await client.create_session(config=session_config)
        print(f"Session created: {session.session_id}")

        # Test 2: Ask the model to summarize its instructions
        prompt = "Please summarize the [Formatting Guidelines] you have been given in a list."

        print(f"\nSending prompt: '{prompt}'")
        response = await session.send_and_wait({"prompt": prompt, "mode": "immediate"})

        print("\n--- Model Response ---")
        content = response.data.content if response and response.data else "No content"
        print(content)
        print("----------------------")

        required_keywords = ["paragraph", "break", "heading", "spacing", "bullet"]
        found_keywords = [kw for kw in required_keywords if kw in content.lower()]

        if len(found_keywords) >= 3:
            print(
                f"\n✅ SUCCESS: Model summarized the guidelines correctly. Found match for: {found_keywords}"
            )
        else:
            print(
                f"\n⚠️ UNCERTAIN: Summary might be generic. Found keywords: {found_keywords}"
            )

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        await client.stop()
        print("\nClient stopped.")


if __name__ == "__main__":
    asyncio.run(main())
