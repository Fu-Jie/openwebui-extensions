#!/usr/bin/env python3
import os
import shutil
import re

def sync_mirrors():
    plugins_root = "plugins"
    docs_root = "docs/plugins"
    
    types = ["actions", "filters", "pipes", "pipelines", "tools"]
    
    for t in types:
        src_type_dir = os.path.join(plugins_root, t)
        dest_type_dir = os.path.join(docs_root, t)
        
        if not os.path.exists(src_type_dir): continue
        os.makedirs(dest_type_dir, exist_ok=True)
        
        for name in os.listdir(src_type_dir):
            plugin_dir = os.path.join(src_type_dir, name)
            if not os.path.isdir(plugin_dir): continue
            
            # Sync README.md -> docs/plugins/{type}/{name}.md
            src_readme = os.path.join(plugin_dir, "README.md")
            if os.path.exists(src_readme):
                dest_readme = os.path.join(dest_type_dir, f"{name}.md")
                shutil.copy(src_readme, dest_readme)
                print(f"✅ Mirrored: {t}/{name} (EN)")
            
            # Sync README_CN.md -> docs/plugins/{type}/{name}.zh.md
            src_readme_cn = os.path.join(plugin_dir, "README_CN.md")
            if os.path.exists(src_readme_cn):
                dest_readme_zh = os.path.join(dest_type_dir, f"{name}.zh.md")
                shutil.copy(src_readme_cn, dest_readme_zh)
                print(f"✅ Mirrored: {t}/{name} (ZH)")

if __name__ == "__main__":
    sync_mirrors()
