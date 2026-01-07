import os
import sys
import json
import requests
import re


def parse_frontmatter(content):
    """Extracts metadata from the python file docstring."""
    # Allow leading whitespace and handle potential shebangs
    match = re.search(r'^\s*"""\n(.*?)\n"""', content, re.DOTALL)
    if not match:
        # Fallback for files starting with comments or shebangs
        match = re.search(r'"""\n(.*?)\n"""', content, re.DOTALL)
        if not match:
            return {}

    frontmatter = match.group(1)
    meta = {}
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta


def sync_frontmatter(file_path, content, meta, post_data):
    """Syncs remote metadata back to local file frontmatter."""
    changed = False
    new_meta = meta.copy()

    # 1. Sync ID
    if "openwebui_id" not in new_meta and "post_id" not in new_meta:
        new_meta["openwebui_id"] = post_data.get("id")
        changed = True

    # 2. Sync Icon URL (often set in UI)
    manifest = (
        post_data.get("data", {})
        .get("function", {})
        .get("meta", {})
        .get("manifest", {})
    )
    if "icon_url" not in new_meta and manifest.get("icon_url"):
        new_meta["icon_url"] = manifest.get("icon_url")
        changed = True

    # 3. Sync other fields if missing locally
    for field in ["author", "author_url", "funding_url"]:
        if field not in new_meta and manifest.get(field):
            new_meta[field] = manifest.get(field)
            changed = True

    if changed:
        print(f"  Syncing metadata back to {os.path.basename(file_path)}...")
        # Reconstruct frontmatter
        # We need to replace the content inside the first """ ... """
        # This is a bit fragile with regex but sufficient for standard files

        def replacement(match):
            lines = []
            # Keep existing description or comments if we can't parse them easily?
            # Actually, let's just reconstruct the key-values we know
            # and try to preserve the description if it was at the end

            # Simple approach: Rebuild the whole block based on new_meta
            # This might lose comments inside the frontmatter, but standard format is simple keys

            # Try to preserve order: title, author, ..., version, ..., description
            ordered_keys = [
                "title",
                "author",
                "author_url",
                "funding_url",
                "version",
                "openwebui_id",
                "icon_url",
                "requirements",
                "description",
            ]

            block = ['"""']

            # Add known keys in order
            for k in ordered_keys:
                if k in new_meta:
                    block.append(f"{k}: {new_meta[k]}")

            # Add any other custom keys
            for k, v in new_meta.items():
                if k not in ordered_keys:
                    block.append(f"{k}: {v}")

            block.append('"""')
            return "\n".join(block)

        new_content = re.sub(
            r'^"""\n(.*?)\n"""', replacement, content, count=1, flags=re.DOTALL
        )

        # If regex didn't match (e.g. leading whitespace), try with whitespace
        if new_content == content:
            new_content = re.sub(
                r'^\s*"""\n(.*?)\n"""', replacement, content, count=1, flags=re.DOTALL
            )

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            return new_content  # Return updated content

    return content


def update_plugin(file_path, post_id, token):
    print(f"Processing {os.path.basename(file_path)} (ID: {post_id})...")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    meta = parse_frontmatter(content)
    if not meta:
        print(f"  Skipping: No frontmatter found.")
        return False

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    # 1. Fetch existing post
    try:
        response = requests.get(
            f"https://api.openwebui.com/api/v1/posts/{post_id}", headers=headers
        )
        response.raise_for_status()
        post_data = response.json()
    except Exception as e:
        print(f"  Error fetching post: {e}")
        return False

    # 1.5 Sync Metadata back to local file
    try:
        content = sync_frontmatter(file_path, content, meta, post_data)
        # Re-parse meta in case it changed
        meta = parse_frontmatter(content)
    except Exception as e:
        print(f"  Warning: Failed to sync local metadata: {e}")

    # 2. Update ONLY Content and Manifest
    try:
        # Ensure structure exists before populating nested fields
        if "data" not in post_data:
            post_data["data"] = {}
        if "function" not in post_data["data"]:
            post_data["data"]["function"] = {}
        if "meta" not in post_data["data"]["function"]:
            post_data["data"]["function"]["meta"] = {}
        if "manifest" not in post_data["data"]["function"]["meta"]:
            post_data["data"]["function"]["meta"]["manifest"] = {}

        # Update 1: The Source Code (Inner Content)
        post_data["data"]["function"]["content"] = content

        # Update 2: The Post Body/README (Outer Content)
        # Try to find a matching README file
        plugin_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path).lower()
        readme_content = None

        # Determine preferred README filename
        readme_files = []
        if base_name.endswith("_cn.py"):
            readme_files = ["README_CN.md", "README.md"]
        else:
            readme_files = ["README.md", "README_CN.md"]

        for readme_name in readme_files:
            readme_path = os.path.join(plugin_dir, readme_name)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r", encoding="utf-8") as f:
                        readme_content = f.read()
                    print(f"  Using README: {readme_name}")
                    break
                except Exception as e:
                    print(f"  Error reading {readme_name}: {e}")

        if readme_content:
            post_data["content"] = readme_content
        elif "description" in meta:
            post_data["content"] = meta["description"]
        else:
            post_data["content"] = ""

        # Update Manifest (Metadata)
        post_data["data"]["function"]["meta"]["manifest"].update(meta)

        # Sync top-level fields for consistency
        if "title" in meta:
            post_data["title"] = meta["title"]
            post_data["data"]["function"]["name"] = meta["title"]
        if "description" in meta:
            post_data["data"]["function"]["meta"]["description"] = meta["description"]

    except Exception as e:
        print(f"  Error preparing update: {e}")
        return False

    # 3. Submit Update
    try:
        response = requests.post(
            f"https://api.openwebui.com/api/v1/posts/{post_id}/update",
            headers=headers,
            json=post_data,
        )
        response.raise_for_status()
        print(f"  ✅ Success!")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False


def main():
    token = os.environ.get("OPENWEBUI_API_KEY")
    if not token:
        print("Error: OPENWEBUI_API_KEY not set.")
        sys.exit(1)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    plugins_dir = os.path.join(base_dir, "plugins")

    count = 0
    # Walk through plugins directory
    for root, _, files in os.walk(plugins_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                # Check for ID in file content without full parse first
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read(
                        2000
                    )  # Read first 2000 chars is enough for frontmatter

                # Simple regex to find ID
                id_match = re.search(
                    r"(?:openwebui_id|post_id):\s*([a-z0-9-]+)", content
                )

                if id_match:
                    post_id = id_match.group(1).strip()
                    update_plugin(file_path, post_id, token)
                    count += 1

    print(f"\nFinished. Updated {count} plugins.")


if __name__ == "__main__":
    main()
