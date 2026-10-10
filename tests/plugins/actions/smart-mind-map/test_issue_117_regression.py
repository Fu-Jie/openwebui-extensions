"""Regression test for issue #117: plugins fail with non-Ollama models.

``generate_chat_completion`` can return a ``JSONResponse`` instead of a dict
(for example for OpenAI-compatible connections). The plugins indexed it like a
dict and failed with ``argument of type 'JSONResponse' is not iterable``.

Covers Smart Mind Map, Smart Infographic and the Smart Mind Map Tool.
"""

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

# Importing the issue #101 test module installs the open_webui stubs and loads
# the Smart Mind Map plugin under test.
from test_issue_101_regression import _noop_emitter, smart_mind_map

REPO_ROOT = Path(__file__).resolve().parents[4]

MIND_MAP_MARKDOWN = "```markdown\n# Topic\n## Branch A\n## Branch B\n```"
INFOGRAPHIC_SYNTAX = "```infographic\ninfographic list-row-simple-horizontal-arrow\ndata\n  items\n    - label Step Alpha\n```"


def _load(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


infographic = _load("infographic_under_test", "plugins/actions/infographic/infographic.py")
smart_mind_map_tool = _load(
    "smart_mind_map_tool_under_test", "plugins/tools/smart-mind-map-tool/smart_mind_map_tool.py"
)


class _FakeJSONResponse:
    """Minimal stand-in for starlette's JSONResponse."""

    def __init__(self, content):
        self.body = json.dumps(content).encode("utf-8")
        self.status_code = 200


def _completion(content: str) -> dict:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def _patch_llm(monkeypatch, module, content: str, *, as_json_response: bool):
    async def fake_generate_chat_completion(request, payload, user):
        completion = _completion(content)
        return _FakeJSONResponse(completion) if as_json_response else completion

    async def fake_call_db(fn, *args, **kwargs):
        return types.SimpleNamespace(id="u1", name="Test")

    monkeypatch.setattr(module, "generate_chat_completion", fake_generate_chat_completion)
    monkeypatch.setattr(module, "_call_db", fake_call_db)


def _action_body() -> dict:
    long_text = "Mind maps organise ideas around a central topic. " * 10
    return {
        "model": "gpt-test",
        "messages": [
            {"id": "msg-user-1", "role": "user", "content": "Summarize."},
            {"id": "msg-asst-1", "role": "assistant", "content": long_text},
        ],
        "chat_id": "chat-1",
        "session_id": "sess-1",
        "id": "msg-asst-1",
    }


USER = {"id": "u1", "name": "Test", "language": "en-US"}


def _rendered(result) -> str:
    return json.dumps(result, default=str, ensure_ascii=False)


@pytest.mark.asyncio
@pytest.mark.parametrize("as_json_response", [True, False])
async def test_smart_mind_map_renders_the_llm_markdown(monkeypatch, as_json_response):
    _patch_llm(monkeypatch, smart_mind_map, MIND_MAP_MARKDOWN, as_json_response=as_json_response)

    result = await smart_mind_map.Action().action(
        _action_body(), __user__=USER, __event_emitter__=_noop_emitter
    )

    html, headers = result
    assert "Branch A" in html and "Branch B" in html
    assert headers["Content-Type"] == "text/html"


@pytest.mark.asyncio
async def test_smart_mind_map_reports_an_unparsable_json_response(monkeypatch):
    class _BrokenResponse:
        body = b"not json"

    async def fake_generate_chat_completion(request, payload, user):
        return _BrokenResponse()

    _patch_llm(monkeypatch, smart_mind_map, MIND_MAP_MARKDOWN, as_json_response=False)
    monkeypatch.setattr(smart_mind_map, "generate_chat_completion", fake_generate_chat_completion)

    body = _action_body()
    result = await smart_mind_map.Action().action(
        body, __user__=USER, __event_emitter__=_noop_emitter
    )

    assert "could not be parsed as JSON" in _rendered(result)


@pytest.mark.asyncio
@pytest.mark.parametrize("as_json_response", [True, False])
async def test_smart_infographic_renders_the_llm_syntax(monkeypatch, as_json_response):
    _patch_llm(monkeypatch, infographic, INFOGRAPHIC_SYNTAX, as_json_response=as_json_response)

    calls = []

    async def event_call(event):
        calls.append(event)

    body = _action_body()
    await infographic.Action().action(
        body, __user__=USER, __event_emitter__=_noop_emitter, __event_call__=event_call
    )

    rendered_code = [c["data"]["code"] for c in calls if c["type"] == "execute"]
    assert any("Step Alpha" in code for code in rendered_code)


@pytest.mark.asyncio
@pytest.mark.parametrize("as_json_response", [True, False])
async def test_smart_mind_map_tool_renders_the_llm_markdown(monkeypatch, as_json_response):
    _patch_llm(monkeypatch, smart_mind_map_tool, MIND_MAP_MARKDOWN, as_json_response=as_json_response)

    result = await smart_mind_map_tool.Tools().generate_mind_map(
        __user__=USER,
        __event_emitter__=_noop_emitter,
        __messages__=[
            {"role": "user", "content": "Explain mind maps."},
            {"role": "assistant", "content": "Mind maps organise ideas around a central topic. " * 10},
        ],
        __metadata__={"model": {"id": "gpt-test"}},
    )

    assert not isinstance(result, str), result
    html = result.body.decode("utf-8")
    assert "Branch A" in html and "Branch B" in html
