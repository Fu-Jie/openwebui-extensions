#!/usr/bin/env python3
import sys
import ast
import os

def check_i18n(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    translations = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "TRANSLATIONS":
                    translations = ast.literal_eval(node.value)
                    break
    
    if not translations:
        print("⚠️ No TRANSLATIONS dictionary found.")
        return

    # Base keys from English
    base_lang = "en-US"
    if base_lang not in translations:
        print(f"❌ Error: {base_lang} missing in TRANSLATIONS.")
        return
    
    base_keys = set(translations[base_lang].keys())
    print(f"🔍 Analyzing {file_path}...")
    print(f"Standard keys ({len(base_keys)}): {', '.join(sorted(base_keys))}
")

    for lang, keys in translations.items():
        if lang == base_lang: continue
        lang_keys = set(keys.keys())
        missing = base_keys - lang_keys
        extra = lang_keys - base_keys
        
        if missing:
            print(f"❌ {lang}: Missing {len(missing)} keys: {', '.join(missing)}")
        if extra:
            print(f"⚠️ {lang}: Has {len(extra)} extra keys: {', '.join(extra)}")
        if not missing and not extra:
            print(f"✅ {lang}: Aligned.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_i18n.py <path_to_plugin.py>")
        sys.exit(1)
    check_i18n(sys.argv[1])
