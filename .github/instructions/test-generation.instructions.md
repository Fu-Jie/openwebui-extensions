---
name: Test Generation
description: Comprehensive Pytest conventions, mocking strategies, and model usage rules for OpenWebUI plugins
applyTo: "plugins/debug/**,tests/**"
---
# Test Generation Instructions

You are an expert SDET (Software Development Engineer in Test) writing tests for the `openwebui-extensions` repository.
Follow these comprehensive guidelines to ensure robust, reliable, and cost-effective testing.

## 1. Test Structure & Placement
- **Unit Tests**: Place in the `tests/` directory at the root of the repository. Name files `test_<module>.py`.
- **Integration/Debug Scripts**: Place in `plugins/debug/<plugin_name>/`. Name files `debug_<feature>.py` or `inspect_<feature>.py`.
- **Fixtures**: Use `conftest.py` for shared fixtures (e.g., mock users, mock emitters, mock database sessions).

## 2. Model Usage & Cost Control (CRITICAL)
When writing tests or debug scripts that actually invoke an LLM:
- **Allowed Models**: You MUST use low-cost models: `gpt-5-mini` (Preferred) or `gpt-4.1`.
- **Forbidden**: NEVER use expensive models (like `gpt-4-turbo`, `claude-3-opus`) in automated tests unless explicitly requested by the user.
- **API Keys**: Never hardcode API keys. Always read from environment variables (`os.getenv("OPENAI_API_KEY")`) or a `.env` file.

## 3. Mocking OpenWebUI Internals
OpenWebUI plugins rely heavily on injected runtime variables. Your tests must mock these accurately:
- **`__user__`**: Mock as a dictionary. Always test both with a full user object and an empty/None object to ensure fallback logic works.
  ```python
  mock_user_en = {"id": "u1", "name": "Alice", "language": "en-US"}
  mock_user_zh = {"id": "u2", "name": "Bob", "language": "zh-CN"}
  mock_user_none = None
  ```
- **`__event_emitter__`**: Mock as an async callable that records emitted events for assertion.
  ```python
  async def mock_emitter(event: dict):
      emitted_events.append(event)
  ```
- **`__event_call__`**: Mock as an async callable. To test Antigravity timeout guards, you must occasionally mock this to sleep longer than the timeout (e.g., `await asyncio.sleep(3.0)`) to ensure `asyncio.wait_for` catches it.

## 4. Testing Async Code
- All OpenWebUI plugin entry points (`action`, `inlet`, `outlet`) are asynchronous.
- Use `@pytest.mark.asyncio` for all test functions.
- Ensure you `await` all plugin method calls.

## 5. i18n (Internationalization) Testing
Since all plugins must be single-file i18n:
- **Mandatory**: Write parameterized tests to verify output in both English (`en-US`) and Chinese (`zh-CN`).
- Verify that if an unsupported language is passed (e.g., `fr-FR`), the system correctly falls back to the default (usually `en-US`).

## 6. Antigravity & Safety Testing
- **Timeout Guards**: Explicitly test that frontend JS executions (`__event_call__`) do not hang the backend. Assert that a `TimeoutError` is caught and handled gracefully.
- **State Leakage**: For `Filter` plugins (which are singletons), write tests that simulate concurrent requests from different users to ensure no state leaks across `self`.

## 7. Assertions & Best Practices
- Assert on **behavior and output**, not internal implementation details.
- For HTML/Markdown generation plugins, use Regex or BeautifulSoup to assert the presence of required tags (e.g., `<!-- OPENWEBUI_PLUGIN_OUTPUT -->`) rather than exact string matching.
- Keep tests isolated. Do not rely on the execution order of tests.
