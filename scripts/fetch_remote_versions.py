import json
import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from openwebui_stats import OpenWebUIStats
except ImportError:
    print("Error: openwebui_stats.py not found.")
    sys.exit(1)


def main():
    # Try to get token from env
    token = os.environ.get("OPENWEBUI_API_KEY")
    if not token:
        print("Error: OPENWEBUI_API_KEY environment variable not set.")
        sys.exit(1)

    print("Fetching remote plugins from OpenWebUI...")
    client = OpenWebUIStats(token)
    try:
        posts = client.get_all_posts()
    except Exception as e:
        print(f"Error fetching posts: {e}")
        sys.exit(1)

    formatted_plugins = []
    for post in posts:
        # Save the full raw post object to ensure we have "compliant update json data"
        # We inject a 'type' field just for the comparison script to know it's remote,
        # but otherwise keep the structure identical to the API response.
        post["type"] = "remote_plugin"
        formatted_plugins.append(post)

    output_file = "remote_versions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(formatted_plugins, f, indent=2, ensure_ascii=False)

    print(
        f"✅ Successfully saved {len(formatted_plugins)} remote plugins to {output_file}"
    )
    print(f"   You can now compare local vs remote using:")
    print(f"   python scripts/extract_plugin_versions.py --compare {output_file}")


if __name__ == "__main__":
    main()
