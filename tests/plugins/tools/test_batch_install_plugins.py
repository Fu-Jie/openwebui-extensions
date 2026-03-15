import asyncio
import importlib.util
import sys
from pathlib import Path

import httpx
import pytest


MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "plugins"
    / "tools"
    / "batch-install-plugins"
    / "batch_install_plugins.py"
)
SPEC = importlib.util.spec_from_file_location("batch_install_plugins", MODULE_PATH)
batch_install_plugins = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = batch_install_plugins
SPEC.loader.exec_module(batch_install_plugins)


def make_candidate(title: str, file_path: str, function_id: str):
    return batch_install_plugins.PluginCandidate(
        plugin_type="tool",
        file_path=file_path,
        metadata={"title": title, "description": f"{title} description"},
        content="class Tools:\n    pass\n",
        function_id=function_id,
    )


def make_request():
    class Request:
        base_url = "http://localhost:3000/"
        headers = {"Authorization": "Bearer token"}

    return Request()


class DummyResponse:
    def __init__(self, status_code: int, json_data=None, text: str = ""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self):
        if self._json_data is None:
            raise ValueError("no json body")
        return self._json_data


class FakeAsyncClient:
    posts = []
    responses = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, headers=None, json=None):
        type(self).posts.append((url, headers, json))
        if not type(self).responses:
            raise AssertionError("No fake response configured for POST request")
        response = type(self).responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class FakeGithubAsyncClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_install_all_plugins_only_installs_filtered_candidates(monkeypatch):
    keep = make_candidate("Keep Plugin", "plugins/tools/keep/keep.py", "keep_plugin")
    exclude = make_candidate(
        "Exclude Me",
        "plugins/tools/exclude-me/exclude_me.py",
        "exclude_me",
    )
    self_plugin = make_candidate(
        "Batch Install Plugins from GitHub",
        "plugins/tools/batch-install-plugins/batch_install_plugins.py",
        "batch_install_plugins",
    )

    async def fake_discover_plugins(url, skip_keywords):
        return [keep, exclude, self_plugin], []

    monkeypatch.setattr(batch_install_plugins, "discover_plugins", fake_discover_plugins)
    FakeAsyncClient.posts = []
    FakeAsyncClient.responses = [DummyResponse(404), DummyResponse(201)]
    monkeypatch.setattr(batch_install_plugins.httpx, "AsyncClient", FakeAsyncClient)

    events = []
    captured = {}

    async def event_call(payload):
        if payload["type"] == "confirmation":
            captured["message"] = payload["data"]["message"]
        elif payload["type"] == "execute":
            captured.setdefault("execute_codes", []).append(payload["data"]["code"])
        return True

    async def emitter(event):
        events.append(event)

    result = await batch_install_plugins.Tools().install_all_plugins(
        __user__={"id": "u1", "language": "en-US"},
        __event_call__=event_call,
        __request__=make_request(),
        __event_emitter__=emitter,
        repo=batch_install_plugins.DEFAULT_REPO,
        plugin_types=["tool"],
        exclude_keywords="exclude",
    )

    assert "Created: Keep Plugin" in result
    assert "Exclude Me" not in result
    assert "1/1" in result
    assert captured["message"].count("[tool]") == 1
    assert "Keep Plugin" in captured["message"]
    assert "Exclude Me" not in captured["message"]
    assert "Batch Install Plugins from GitHub" not in captured["message"]
    assert "exclude, batch-install-plugins" in captured["message"]

    urls = [url for url, _, _ in FakeAsyncClient.posts]
    assert urls == [
        "http://localhost:3000/api/v1/tools/id/keep_plugin/update",
        "http://localhost:3000/api/v1/tools/create",
    ]
    assert any(
        "Starting OpenWebUI install requests" in code
        for code in captured.get("execute_codes", [])
    )
    assert events[-1]["type"] == "notification"
    assert events[-1]["data"]["type"] == "success"


@pytest.mark.asyncio
async def test_install_all_plugins_supports_missing_event_emitter(monkeypatch):
    keep = make_candidate("Keep Plugin", "plugins/tools/keep/keep.py", "keep_plugin")

    async def fake_discover_plugins(url, skip_keywords):
        return [keep], []

    monkeypatch.setattr(batch_install_plugins, "discover_plugins", fake_discover_plugins)
    FakeAsyncClient.posts = []
    FakeAsyncClient.responses = [DummyResponse(404), DummyResponse(201)]
    monkeypatch.setattr(batch_install_plugins.httpx, "AsyncClient", FakeAsyncClient)

    result = await batch_install_plugins.Tools().install_all_plugins(
        __user__={"id": "u1", "language": "en-US"},
        __request__=make_request(),
        repo="example/repo",
        plugin_types=["tool"],
    )

    assert "Created: Keep Plugin" in result
    assert "1/1" in result


@pytest.mark.asyncio
async def test_install_all_plugins_handles_confirmation_timeout(monkeypatch):
    keep = make_candidate("Keep Plugin", "plugins/tools/keep/keep.py", "keep_plugin")

    async def fake_discover_plugins(url, skip_keywords):
        return [keep], []

    async def fake_wait_for(awaitable, timeout):
        awaitable.close()
        raise asyncio.TimeoutError

    monkeypatch.setattr(batch_install_plugins, "discover_plugins", fake_discover_plugins)
    monkeypatch.setattr(batch_install_plugins.asyncio, "wait_for", fake_wait_for)

    events = []

    async def event_call(payload):
        return True

    async def emitter(event):
        events.append(event)

    result = await batch_install_plugins.Tools().install_all_plugins(
        __user__={"id": "u1", "language": "en-US"},
        __event_call__=event_call,
        __request__=make_request(),
        __event_emitter__=emitter,
        repo="example/repo",
        plugin_types=["tool"],
    )

    assert result == "Confirmation timed out or failed. Installation cancelled."
    assert events[-1]["type"] == "notification"
    assert events[-1]["data"]["type"] == "warning"


@pytest.mark.asyncio
async def test_install_all_plugins_marks_total_failure_as_error(monkeypatch):
    keep = make_candidate("Keep Plugin", "plugins/tools/keep/keep.py", "keep_plugin")

    async def fake_discover_plugins(url, skip_keywords):
        return [keep], []

    monkeypatch.setattr(batch_install_plugins, "discover_plugins", fake_discover_plugins)
    FakeAsyncClient.posts = []
    FakeAsyncClient.responses = [
        DummyResponse(500, {"detail": "update failed"}, "update failed"),
        DummyResponse(500, {"detail": "create failed"}, "create failed"),
    ]
    monkeypatch.setattr(batch_install_plugins.httpx, "AsyncClient", FakeAsyncClient)

    events = []

    async def emitter(event):
        events.append(event)

    result = await batch_install_plugins.Tools().install_all_plugins(
        __user__={"id": "u1", "language": "en-US"},
        __request__=make_request(),
        __event_emitter__=emitter,
        repo="example/repo",
        plugin_types=["tool"],
    )

    assert "Failed: Keep Plugin - status 500:" in result
    assert "0/1" in result
    assert events[-1]["type"] == "notification"
    assert events[-1]["data"]["type"] == "error"


@pytest.mark.asyncio
async def test_install_all_plugins_localizes_timeout_errors(monkeypatch):
    keep = make_candidate("Keep Plugin", "plugins/tools/keep/keep.py", "keep_plugin")

    async def fake_discover_plugins(url, skip_keywords):
        return [keep], []

    monkeypatch.setattr(batch_install_plugins, "discover_plugins", fake_discover_plugins)
    FakeAsyncClient.posts = []
    FakeAsyncClient.responses = [httpx.TimeoutException("timed out")]
    monkeypatch.setattr(batch_install_plugins.httpx, "AsyncClient", FakeAsyncClient)

    result = await batch_install_plugins.Tools().install_all_plugins(
        __user__={"id": "u1", "language": "zh-CN"},
        __request__=make_request(),
        repo="example/repo",
        plugin_types=["tool"],
    )

    assert "失败：Keep Plugin - 请求超时" in result


@pytest.mark.asyncio
async def test_install_all_plugins_emits_frontend_debug_logs_on_connect_error(
    monkeypatch,
):
    keep = make_candidate("Keep Plugin", "plugins/tools/keep/keep.py", "keep_plugin")

    async def fake_discover_plugins(url, skip_keywords):
        return [keep], []

    monkeypatch.setattr(batch_install_plugins, "discover_plugins", fake_discover_plugins)
    FakeAsyncClient.posts = []
    # Both initial attempt and fallback retry should fail
    FakeAsyncClient.responses = [httpx.ConnectError("connect failed"), httpx.ConnectError("connect failed")]
    monkeypatch.setattr(batch_install_plugins.httpx, "AsyncClient", FakeAsyncClient)

    execute_codes = []
    events = []

    async def event_call(payload):
        if payload["type"] == "execute":
            execute_codes.append(payload["data"]["code"])
            return True
        if payload["type"] == "confirmation":
            return True
        raise AssertionError(f"Unexpected event_call payload type: {payload['type']}")

    async def emitter(event):
        events.append(event)

    result = await batch_install_plugins.Tools().install_all_plugins(
        __user__={"id": "u1", "language": "en-US"},
        __event_call__=event_call,
        __request__=make_request(),
        __event_emitter__=emitter,
        repo="example/repo",
        plugin_types=["tool"],
    )

    assert result == "Cannot connect to OpenWebUI. Is it running?"
    assert any("OpenWebUI connection failed" in code for code in execute_codes)
    assert any("console.error" in code for code in execute_codes)
    assert any("http://localhost:3000" in code for code in execute_codes)
    assert events[-1]["type"] == "notification"
    assert events[-1]["data"]["type"] == "error"


def test_extract_metadata_supports_crlf_and_folded_yaml_docstrings():
    content = (
        '"""\r\n'
        "title: Persona Selector\r\n"
        "author: ichrist\r\n"
        "description: >\r\n"
        "  Two-step persona picker. Step 1: numbered category list (16 categories).\r\n"
        "  Step 2: numbered persona list (10 per category). 160 personas + Custom.\r\n"
        "version: 6.0.2\r\n"
        '"""\r\n\r\n'
        "class Tools:\r\n"
        "    pass\r\n"
    )

    metadata = batch_install_plugins.extract_metadata(content)

    assert metadata["title"] == "Persona Selector"
    assert metadata["author"] == "ichrist"
    assert metadata["version"] == "6.0.2"
    assert metadata["description"] == (
        "Two-step persona picker. Step 1: numbered category list (16 categories). "
        "Step 2: numbered persona list (10 per category). 160 personas + Custom."
    )


@pytest.mark.asyncio
async def test_discover_plugins_supports_community_repo_crlf_docstrings(monkeypatch):
    tree = [
        {"type": "blob", "path": "Tools/ask-user.py"},
        {"type": "blob", "path": "Tools/persona.py"},
        {"type": "blob", "path": "Tools/orchestrator.py"},
    ]
    contents = {
        "Tools/ask-user.py": (
            '"""\r\n'
            "title: Ask User\r\n"
            "author: ichrist\r\n"
            "version: 1.0\r\n"
            "description: Allows the LLM to autonomously trigger 1-5 interactive pop-up questions.\r\n"
            '"""\r\n\r\n'
            "class Tools:\r\n"
            "    pass\r\n"
        ),
        "Tools/persona.py": (
            '"""\r\n'
            "title: Persona Selector\r\n"
            "author: ichrist\r\n"
            "description: >\r\n"
            "  Two-step persona picker. Step 1: numbered category list (16 categories).\r\n"
            "  Step 2: numbered persona list (10 per category). 160 personas + Custom.\r\n"
            "version: 6.0.2\r\n"
            '"""\r\n\r\n'
            "class Tools:\r\n"
            "    pass\r\n"
        ),
        "Tools/orchestrator.py": (
            '"""\r\n'
            "title: 🌌 The Omniscient Orchestrator\r\n"
            "author: ichrist\r\n"
            "version: 2.0\r\n"
            "description: A high-polish, multi-stage workflow engine.\r\n"
            '"""\r\n\r\n'
            "class Tools:\r\n"
            "    pass\r\n"
        ),
    }

    async def fake_fetch_tree(client, owner, repo, branch):
        assert (owner, repo, branch) == ("iChristGit", "OpenWebui-Tools", "main")
        return tree

    async def fake_fetch_file(client, owner, repo, branch, path):
        return contents[path]

    monkeypatch.setattr(batch_install_plugins.httpx, "AsyncClient", FakeGithubAsyncClient)
    monkeypatch.setattr(batch_install_plugins, "fetch_github_tree", fake_fetch_tree)
    monkeypatch.setattr(batch_install_plugins, "fetch_github_file", fake_fetch_file)

    candidates, skipped = await batch_install_plugins.discover_plugins(
        "https://github.com/iChristGit/OpenWebui-Tools/",
        batch_install_plugins.DEFAULT_SKIP_KEYWORDS,
    )

    assert sorted(candidate.title for candidate in candidates) == [
        "Ask User",
        "Persona Selector",
        "🌌 The Omniscient Orchestrator",
    ]
    assert skipped == []
