#!/usr/bin/env python3
import sys
import os


def scaffold(p_type, p_name, title, desc):
    target_dir = f"plugins/{p_type}/{p_name}"
    os.makedirs(target_dir, exist_ok=True)

    class_name = (
        "Action"
        if p_type == "actions"
        else (
            "Filter"
            if p_type == "filters"
            else "Tools" if p_type == "tools" else "Pipe"
        )
    )
    method_name = (
        "action"
        if p_type == "actions"
        else (
            "outlet"
            if p_type == "filters"
            else "execute" if p_type == "tools" else "pipe"
        )
    )

    replacements = {
        "{{TITLE}}": title,
        "{{DESCRIPTION}}": desc,
        "{{CLASS_NAME}}": class_name,
        "{{METHOD_NAME}}": method_name,
    }

    # Files to generate
    templates = [
        ("assets/template.py.j2", f"{p_name}.py"),
        ("assets/README_template.md", "README.md"),
        ("assets/README_template.md", "README_CN.md"),
    ]

    # Path relative to skill root
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    for t_path, t_name in templates:
        template_file = os.path.join(skill_root, t_path)
        if not os.path.exists(template_file):
            print(f"⚠️ Warning: Template not found {template_file}")
            continue

        with open(template_file, "r") as f:
            content = f.read()
        for k, v in replacements.items():
            content = content.replace(k, v)

        with open(os.path.join(target_dir, t_name), "w") as f:
            f.write(content)
        print(f"✅ Generated: {target_dir}/{t_name}")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: scaffold.py <type> <name> <title> <desc>")
        sys.exit(1)
    scaffold(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
