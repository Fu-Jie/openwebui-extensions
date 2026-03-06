import asyncio
import json
import sys
from typing import Any, Callable

from copilot import CopilotClient

try:
    from copilot import PermissionHandler
except ImportError:
    PermissionHandler = None


def _to_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        return to_dict()
    if isinstance(obj, dict):
        return obj
    result = {}
    for key in ("name", "display_name", "description"):
        if hasattr(obj, key):
            result[key] = getattr(obj, key)
    return result


def _extract_agents(result: Any) -> list[dict]:
    if result is None:
        return []

    if isinstance(result, dict):
        raw_agents = result.get("agents")
    else:
        raw_agents = getattr(result, "agents", None)

    if not raw_agents:
        return []

    normalized = []
    for item in raw_agents:
        data = _to_dict(item)
        normalized.append(
            {
                "name": str(data.get("name", "") or "").strip(),
                "display_name": str(data.get("display_name", "") or "").strip(),
                "description": str(data.get("description", "") or "").strip(),
            }
        )
    return normalized


def _extract_current_agent(result: Any) -> dict | None:
    if result is None:
        return None

    if isinstance(result, dict):
        agent = result.get("agent")
    else:
        agent = getattr(result, "agent", None)

    if not agent:
        return None

    data = _to_dict(agent)
    return {
        "name": str(data.get("name", "") or "").strip(),
        "display_name": str(data.get("display_name", "") or "").strip(),
        "description": str(data.get("description", "") or "").strip(),
    }


async def main() -> int:
    client = CopilotClient()
    started = False
    session = None

    try:
        await client.start()
        started = True

        session_config: dict[str, Any] = {}
        permission_handler: Callable | None = getattr(
            PermissionHandler, "approve_all", None
        )
        if callable(permission_handler):
            session_config["on_permission_request"] = permission_handler

        session = await client.create_session(session_config)

        list_result = await session.rpc.agent.list()
        current_result = await session.rpc.agent.get_current()

        agents = _extract_agents(list_result)
        current = _extract_current_agent(current_result)

        payload = {
            "agents_count": len(agents),
            "agents": agents,
            "current_agent": current,
            "summary": (
                "No custom agents detected in current runtime."
                if not agents
                else "Custom agents detected."
            ),
        }

        print(json.dumps(payload, ensure_ascii=False, indent=2))

        if not agents:
            print("\n[INFO] 当前运行时没有已注入的 custom agents（默认通常为空）。")
        elif not current:
            print("\n[INFO] 已检测到 custom agents，但当前没有选中的 agent。")
        else:
            print(
                "\n[INFO] 当前已选中 agent: "
                f"{current.get('display_name') or current.get('name') or '(unknown)'}"
            )

        return 0

    except Exception as exc:
        print(f"[ERROR] Agent 检测失败: {exc}", file=sys.stderr)
        return 1

    finally:
        if session is not None:
            try:
                await session.destroy()
            except Exception:
                pass

        if started:
            try:
                await client.stop()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
