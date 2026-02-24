#!/usr/bin/env python3
import sys
import os
import re
from datetime import datetime

def patch_file(file_path, old_pattern, new_content, is_regex=False):
    if not os.path.exists(file_path):
        print(f"Warning: File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if is_regex:
        new_content_result = re.sub(old_pattern, new_content, content, flags=re.MULTILINE)
    else:
        new_content_result = content.replace(old_pattern, new_content)
    
    if new_content_result != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content_result)
        print(f"✅ Patched: {file_path}")
        return True
    else:
        print(f"ℹ️ No change needed: {file_path}")
        return False

def bump_version(plugin_type, plugin_name, new_version, msg_en, msg_zh):
    print(f"🚀 Bumping {plugin_name} ({plugin_type}) to {new_version}...")
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_badge = today.replace("-", "--")
    
    # 1. Patch Plugin Python File
    py_file = f"plugins/{plugin_type}/{plugin_name}/{plugin_name}.py"
    patch_file(py_file, r"version: \d+\.\d+\.\d+", f"version: {new_version}", is_regex=True)
    
    # 2. Patch Plugin READMEs
    readme_en = f"plugins/{plugin_type}/{plugin_name}/README.md"
    readme_zh = f"plugins/{plugin_type}/{plugin_name}/README_CN.md"
    
    # Update version in metadata
    patch_file(readme_en, r"\*\*Version:\*\* \d+\.\d+\.\d+", f"**Version:** {new_version}", is_regex=True)
    patch_file(readme_zh, r"\*\*版本:\*\* \d+\.\d+\.\d+", f"**版本:** {new_version}", is_regex=True)
    
    # Update What's New (Assuming standard headers)
    patch_file(readme_en, r"## 🔥 What's New in v.*?\n", f"## 🔥 What's New in v{new_version}\n\n* {msg_en}\n", is_regex=True)
    patch_file(readme_zh, r"## 🔥 最新更新 v.*?\n", f"## 🔥 最新更新 v{new_version}\n\n* {msg_zh}\n", is_regex=True)
    
    # 3. Patch Docs Mirrors
    doc_en = f"docs/plugins/{plugin_type}/{plugin_name}.md"
    doc_zh = f"docs/plugins/{plugin_type}/{plugin_name}.zh.md"
    patch_file(doc_en, r"\*\*Version:\*\* \d+\.\d+\.\d+", f"**Version:** {new_version}", is_regex=True)
    patch_file(doc_zh, r"\*\*版本:\*\* \d+\.\d+\.\d+", f"**版本:** {new_version}", is_regex=True)
    
    # 4. Patch Root READMEs (Updated Date Badge)
    patch_file("README.md", r"badge/202\d--\d\d--\d\d-gray", f"badge/{today_badge}-gray", is_regex=True)
    patch_file("README_CN.md", r"badge/202\d--\d\d--\d\d-gray", f"badge/{today_badge}-gray", is_regex=True)

    print("\n✨ All synchronization tasks completed.")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: bump.py <type> <name> <version> <msg_en> <msg_zh>")
        print("Example: bump.py filters markdown_normalizer 1.2.8 'Fix bug' '修复错误'")
        sys.exit(1)
    
    bump_version(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
