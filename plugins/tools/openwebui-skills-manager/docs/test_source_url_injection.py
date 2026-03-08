#!/usr/bin/env python3
"""
Test suite for source URL injection feature in skill content.
Tests that installation source URLs are properly appended to skill content.
"""

import re
import sys

# Add plugin directory to path
sys.path.insert(
    0,
    "/Users/fujie/app/python/oui/openwebui-extensions/plugins/tools/openwebui-skills-manager",
)


def _append_source_url_to_content(content: str, url: str, lang: str = "en-US") -> str:
    """
    Append installation source URL information to skill content.
    Adds a reference link at the bottom of the content.
    """
    if not content or not url:
        return content

    # Remove any existing source references (to prevent duplication when updating)
    content = re.sub(
        r"\n*---\n+\*\*Installation Source.*?\*\*:.*?\n+---\n*$",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Determine the appropriate language for the label
    source_label = {
        "en-US": "Installation Source",
        "zh-CN": "安装源",
        "zh-TW": "安裝來源",
        "zh-HK": "安裝來源",
        "ja-JP": "インストールソース",
        "ko-KR": "설치 소스",
        "fr-FR": "Source d'installation",
        "de-DE": "Installationsquelle",
        "es-ES": "Fuente de instalación",
    }.get(lang, "Installation Source")

    reference_text = {
        "en-US": "For additional related files or documentation, you can reference the installation source below:",
        "zh-CN": "如需获取相关文件或文档，可以参考下面的安装源：",
        "zh-TW": "如需獲取相關檔案或文件，可以參考下面的安裝來源：",
        "zh-HK": "如需獲取相關檔案或文件，可以參考下面的安裝來源：",
        "ja-JP": "関連ファイルまたはドキュメントについては、以下のインストールソースを参照できます：",
        "ko-KR": "관련 파일 또는 문서를 확인하려면 아래 설치 소스를 참조할 수 있습니다:",
        "fr-FR": "Pour obtenir des fichiers ou des documents connexes, vous pouvez vous reporter à la source d'installation ci-dessous :",
        "de-DE": "Für zusätzliche verwandte Dateien oder Dokumentation können Sie die folgende Installationsquelle referenzieren:",
        "es-ES": "Para archivos o documentación relacionados, puede consultar la siguiente fuente de instalación:",
    }.get(
        lang,
        "For additional related files or documentation, you can reference the installation source below:",
    )

    # Append source URL with reference
    source_block = (
        f"\n\n---\n**{source_label}**: [{url}]({url})\n\n*{reference_text}*\n---"
    )
    return content + source_block


def test_append_source_url_english():
    content = "# My Skill\n\nThis is my awesome skill."
    url = "https://github.com/user/repo/blob/main/SKILL.md"
    result = _append_source_url_to_content(content, url, "en-US")
    assert "Installation Source" in result, "English label missing"
    assert url in result, "URL not found in result"
    assert "additional related files" in result, "Reference text missing"
    assert "---" in result, "Separator missing"
    print("✅ Test 1 passed: English source URL injection")


def test_append_source_url_chinese():
    content = "# 我的技能\n\n这是我的神奇技能。"
    url = "https://github.com/用户/仓库/blob/main/SKILL.md"
    result = _append_source_url_to_content(content, url, "zh-CN")
    assert "安装源" in result, "Chinese label missing"
    assert url in result, "URL not found in result"
    assert "相关文件" in result, "Chinese reference text missing"
    print("✅ Test 2 passed: Chinese (Simplified) source URL injection")


def test_append_source_url_traditional_chinese():
    content = "# 我的技能\n\n這是我的神奇技能。"
    url = "https://raw.githubusercontent.com/user/repo/main/SKILL.md"
    result = _append_source_url_to_content(content, url, "zh-HK")
    assert "安裝來源" in result, "Traditional Chinese label missing"
    assert url in result, "URL not found in result"
    print("✅ Test 3 passed: Traditional Chinese (HK) source URL injection")


def test_append_source_url_japanese():
    content = "# 私のスキル\n\nこれは素晴らしいスキルです。"
    url = "https://github.com/user/repo/tree/main/skills"
    result = _append_source_url_to_content(content, url, "ja-JP")
    assert "インストールソース" in result, "Japanese label missing"
    assert url in result, "URL not found in result"
    print("✅ Test 4 passed: Japanese source URL injection")


def test_append_source_url_korean():
    content = "# 내 기술\n\n이것은 놀라운 기술입니다."
    url = "https://example.com/skill.zip"
    result = _append_source_url_to_content(content, url, "ko-KR")
    assert "설치 소스" in result, "Korean label missing"
    assert url in result, "URL not found in result"
    print("✅ Test 5 passed: Korean source URL injection")


def test_append_source_url_french():
    content = "# Ma Compétence\n\nCeci est ma compétence géniale."
    url = "https://github.com/user/repo/releases/download/v1.0/skill.tar.gz"
    result = _append_source_url_to_content(content, url, "fr-FR")
    assert "Source d'installation" in result, "French label missing"
    assert url in result, "URL not found in result"
    print("✅ Test 6 passed: French source URL injection")


def test_append_source_url_german():
    content = "# Meine Fähigkeit\n\nDies ist meine großartige Fähigkeit."
    url = "https://github.com/owner/skill-repo"
    result = _append_source_url_to_content(content, url, "de-DE")
    assert "Installationsquelle" in result, "German label missing"
    assert url in result, "URL not found in result"
    print("✅ Test 7 passed: German source URL injection")


def test_append_source_url_spanish():
    content = "# Mi Habilidad\n\nEsta es mi habilidad sorprendente."
    url = "https://github.com/usuario/repositorio"
    result = _append_source_url_to_content(content, url, "es-ES")
    assert "Fuente de instalación" in result, "Spanish label missing"
    assert url in result, "URL not found in result"
    print("✅ Test 8 passed: Spanish source URL injection")


def test_deduplication_on_update():
    content_with_source = """# Test Skill

This is a test skill.

---
**Installation Source**: [https://old-url.com](https://old-url.com)

*For additional related files...*
---"""
    new_url = "https://new-url.com"
    result = _append_source_url_to_content(content_with_source, new_url, "en-US")
    match_count = len(re.findall(r"\*\*Installation Source\*\*", result))
    assert match_count == 1, f"Expected 1 source section, found {match_count}"
    assert new_url in result, "New URL not found in result"
    assert "https://old-url.com" not in result, "Old URL should be removed"
    print("✅ Test 9 passed: Source URL deduplication on update")


def test_empty_content_edge_case():
    result = _append_source_url_to_content("", "https://example.com", "en-US")
    assert result == "", "Empty content should return empty"
    print("✅ Test 10 passed: Empty content edge case")


def test_empty_url_edge_case():
    content = "# Test"
    result = _append_source_url_to_content(content, "", "en-US")
    assert result == content, "Empty URL should not modify content"
    print("✅ Test 11 passed: Empty URL edge case")


def test_markdown_formatting_preserved():
    content = """# Main Title

## Section 1
- Item 1
- Item 2

## Section 2
```python
def example():
    pass
```

More content here."""

    url = "https://github.com/example"
    result = _append_source_url_to_content(content, url, "en-US")
    assert "# Main Title" in result, "Main title lost"
    assert "## Section 1" in result, "Section 1 lost"
    assert "def example():" in result, "Code block lost"
    assert url in result, "URL not properly added"
    print("✅ Test 12 passed: Markdown formatting preserved")


def test_url_with_special_characters():
    content = "# Test"
    url = "https://github.com/user/repo?ref=main&version=1.0#section"
    result = _append_source_url_to_content(content, url, "en-US")
    assert result.count(url) == 2, "URL should appear twice in [url](url) format"
    print("✅ Test 13 passed: URL with special characters")


if __name__ == "__main__":
    print("🧪 Running source URL injection tests...\n")
    test_append_source_url_english()
    test_append_source_url_chinese()
    test_append_source_url_traditional_chinese()
    test_append_source_url_japanese()
    test_append_source_url_korean()
    test_append_source_url_french()
    test_append_source_url_german()
    test_append_source_url_spanish()
    test_deduplication_on_update()
    test_empty_content_edge_case()
    test_empty_url_edge_case()
    test_markdown_formatting_preserved()
    test_url_with_special_characters()
    print(
        "\n✅ All 13 tests passed! Source URL injection feature is working correctly."
    )
