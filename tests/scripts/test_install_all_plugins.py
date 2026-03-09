import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "install_all_plugins.py"
SPEC = importlib.util.spec_from_file_location("install_all_plugins", MODULE_PATH)
install_all_plugins = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = install_all_plugins
SPEC.loader.exec_module(install_all_plugins)


PLUGIN_HEADER = '''"""
title: Example Plugin
version: 1.0.0
openwebui_id: 12345678-1234-1234-1234-123456789abc
description: Example description.
"""
'''


def write_plugin(path: Path, header: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\nclass Action:\n    pass\n", encoding="utf-8")


def test_should_skip_plugin_file_filters_localized_and_helper_names():
    assert (
        install_all_plugins.should_skip_plugin_file(Path("flash_card_cn.py"))
        == "localized _cn file"
    )
    assert (
        install_all_plugins.should_skip_plugin_file(Path("verify_generation.py"))
        == "test or helper script"
    )
    assert (
        install_all_plugins.should_skip_plugin_file(Path("测试.py"))
        == "non-ascii filename"
    )
    assert install_all_plugins.should_skip_plugin_file(Path("flash_card.py")) is None


def test_build_function_id_prefers_id_then_title_then_filename():
    from_id = install_all_plugins.build_function_id(
        Path("dummy.py"), {"id": "Async Context Compression"}
    )
    from_title = install_all_plugins.build_function_id(
        Path("dummy.py"), {"title": "GitHub Copilot Official SDK Pipe"}
    )
    from_file = install_all_plugins.build_function_id(Path("dummy_plugin.py"), {})

    assert from_id == "async_context_compression"
    assert from_title == "github_copilot_official_sdk_pipe"
    assert from_file == "dummy_plugin"


def test_build_payload_uses_native_tool_shape_for_tools():
    candidate = install_all_plugins.PluginCandidate(
        plugin_type="tool",
        file_path=Path("plugins/tools/demo/demo_tool.py"),
        metadata={
            "title": "Demo Tool",
            "description": "Demo tool description",
            "openwebui_id": "12345678-1234-1234-1234-123456789abc",
        },
        content='class Tools:\n    pass\n',
        function_id="demo_tool",
    )

    payload = install_all_plugins.build_payload(candidate)

    assert payload == {
        "id": "demo_tool",
        "name": "Demo Tool",
        "meta": {
            "description": "Demo tool description",
            "manifest": {},
        },
        "content": 'class Tools:\n    pass\n',
        "access_grants": [],
    }


def test_build_api_urls_uses_tool_endpoints_for_tools():
    candidate = install_all_plugins.PluginCandidate(
        plugin_type="tool",
        file_path=Path("plugins/tools/demo/demo_tool.py"),
        metadata={"title": "Demo Tool"},
        content='class Tools:\n    pass\n',
        function_id="demo_tool",
    )

    update_url, create_url = install_all_plugins.build_api_urls(
        "http://localhost:3000", candidate
    )

    assert update_url == "http://localhost:3000/api/v1/tools/id/demo_tool/update"
    assert create_url == "http://localhost:3000/api/v1/tools/create"


def test_discover_plugins_only_returns_supported_openwebui_plugins(tmp_path, monkeypatch):
    actions_dir = tmp_path / "plugins" / "actions"
    filters_dir = tmp_path / "plugins" / "filters"
    pipes_dir = tmp_path / "plugins" / "pipes"
    tools_dir = tmp_path / "plugins" / "tools"

    write_plugin(actions_dir / "flash-card" / "flash_card.py", PLUGIN_HEADER)
    write_plugin(actions_dir / "flash-card" / "flash_card_cn.py", PLUGIN_HEADER)
    write_plugin(actions_dir / "infographic" / "verify_generation.py", PLUGIN_HEADER)
    write_plugin(filters_dir / "missing-id" / "missing_id.py", '"""\ntitle: Missing ID\n"""\n')
    write_plugin(pipes_dir / "sdk" / "github_copilot_sdk.py", PLUGIN_HEADER)
    write_plugin(tools_dir / "skills" / "openwebui_skills_manager.py", PLUGIN_HEADER)

    monkeypatch.setattr(
        install_all_plugins,
        "PLUGIN_TYPE_DIRS",
        {
            "action": actions_dir,
            "filter": filters_dir,
            "pipe": pipes_dir,
            "tool": tools_dir,
        },
    )
    monkeypatch.setattr(install_all_plugins, "REPO_ROOT", tmp_path)

    candidates, skipped = install_all_plugins.discover_plugins(
        ["action", "filter", "pipe", "tool"]
    )

    candidate_names = [candidate.file_path.name for candidate in candidates]
    skipped_reasons = {path.name: reason for path, reason in skipped}

    assert candidate_names == [
        "flash_card.py",
        "github_copilot_sdk.py",
        "openwebui_skills_manager.py",
    ]
    assert skipped_reasons["missing_id.py"] == "missing openwebui_id"
    assert skipped_reasons["flash_card_cn.py"] == "localized _cn file"
    assert skipped_reasons["verify_generation.py"] == "test or helper script"


@pytest.mark.parametrize(
    ("header", "expected_reason"),
    [
        ('"""\ntitle: Missing ID\n"""\n', "missing openwebui_id"),
        ("class Action:\n    pass\n", "missing plugin header"),
    ],
)
def test_discover_plugins_reports_missing_metadata(tmp_path, monkeypatch, header, expected_reason):
    action_dir = tmp_path / "plugins" / "actions"
    plugin_file = action_dir / "demo" / "demo.py"
    write_plugin(plugin_file, header)

    monkeypatch.setattr(
        install_all_plugins,
        "PLUGIN_TYPE_DIRS",
        {
            "action": action_dir,
            "filter": tmp_path / "plugins" / "filters",
            "pipe": tmp_path / "plugins" / "pipes",
            "tool": tmp_path / "plugins" / "tools",
        },
    )
    monkeypatch.setattr(install_all_plugins, "REPO_ROOT", tmp_path)

    candidates, skipped = install_all_plugins.discover_plugins(["action"])

    assert candidates == []
    assert skipped == [(plugin_file, expected_reason)]
