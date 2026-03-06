import sys
import importlib.util
import os


def check_i18n(file_path):
    """
    Check if all language keys are synchronized across all translations in a plugin.
    Always uses en-US as the source of truth.
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # Dynamically import the plugin's Pipe class
    spec = importlib.util.spec_from_file_location("github_copilot_sdk", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    pipe = module.Pipe()
    translations = pipe.TRANSLATIONS

    # en-US is our baseline
    en_keys = set(translations["en-US"].keys())
    print(f"Comparing all languages against en-US baseline ({len(en_keys)} keys)...")
    print(f"Found {len(translations)} languages: {', '.join(translations.keys())}")

    all_good = True
    for lang, trans in translations.items():
        if lang == "en-US":
            continue

        lang_keys = set(trans.keys())
        missing = en_keys - lang_keys
        extra = lang_keys - en_keys

        if missing:
            all_good = False
            print(f"\n[{lang}] 🔴 MISSING keys: {missing}")

        if extra:
            all_good = False
            print(f"[{lang}] 🔵 EXTRA keys: {extra}")

    if all_good:
        print("\n✅ All translations are fully synchronized!")
    else:
        print("\n❌ Translation sync check failed.")


if __name__ == "__main__":
    # Get the parent path of this script to find the plugin relative to it
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_plugin = os.path.join(base_path, "github_copilot_sdk.py")

    check_i18n(target_plugin)
