"""Regression test for issue #117: Smart Mind Map fails with non-Ollama models.

``generate_chat_completion`` can return a ``JSONResponse`` instead of a dict
(for example for OpenAI-compatible connections). The action indexed it like a
dict and failed with ``argument of type 'JSONResponse' is not iterable``.
"""

import json
import types

import pytest

# Importing the issue #101 test module installs the open_webui stubs and loads
# the plugin under test.
from test_issue_101_regression import _noop_emitter, smart_mind_map

MIND_MAP_MARKDOWN = "```markdown\n# Topic\n## Branch A\n## Branch B\n```"


class _FakeJSONResponse:
    """Minimal stand-in for starlette's JSONResponse."""

    def __init__(self, content):
        self.body = json.dumps(content).encode("utf-8")
        self.status_code = 200


@pytest.mark.asyncio
async def test_action_reads_a_json_response_from_generate_chat_completion(monkeypatch):
    calls = []

    async def fake_generate_chat_completion(request, payload, user):
        calls.append(payload)
        return _FakeJSONResponse(
            {"choices": [{"message": {"role": "assistant", "content": MIND_MAP_MARKDOWN}}]}
        )

    async def fake_call_db(fn, *args, **kwargs):
        return types.SimpleNamespace(id="u1", name="Test")

    monkeypatch.setattr(smart_mind_map, "generate_chat_completion", fake_generate_chat_completion)
    monkeypatch.setattr(smart_mind_map, "_call_db", fake_call_db)

    action = smart_mind_map.Action()
    long_text = "Mind maps organise ideas around a central topic. " * 10
    body = {
        "model": "gpt-test",
        "messages": [
            {"id": "msg-user-1", "role": "user", "content": "Summarize."},
            {"id": "msg-asst-1", "role": "assistant", "content": long_text},
        ],
        "chat_id": "chat-1",
        "session_id": "sess-1",
        "id": "msg-asst-1",
    }

    result = await action.action(
        body,
        __user__={"id": "u1", "name": "Test", "language": "en-US"},
        __event_emitter__=_noop_emitter,
    )

    assert calls, "the LLM was never called"
    rendered = json.dumps(result, default=str) if result is not None else ""
    assert "is not iterable" not in rendered
    assert "LLM response format is incorrect" not in rendered
