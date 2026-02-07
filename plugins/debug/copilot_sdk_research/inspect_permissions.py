import inspect
import json

try:
    import copilot
    from copilot import types

    print(f"Copilot location: {copilot.__file__}")

    print("\n=== Inspecting PermissionRequest types ===")
    # Look for definition of PermissionRequest or similar

    # In the absence of direct access to the CLI output structure documentation,
    # we can check if there are type hints or typed dicts in copilot.types

    for name, obj in inspect.getmembers(types):
        if "Permission" in name or "Request" in name:
            print(f"\nType: {name}")
            try:
                if hasattr(obj, "__annotations__"):
                    print(obj.__annotations__)
            except:
                pass

except ImportError:
    print("copilot module not installed")
