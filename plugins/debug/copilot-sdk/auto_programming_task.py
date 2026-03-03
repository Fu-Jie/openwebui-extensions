#!/usr/bin/env python3
"""
Run an autonomous programming task via Copilot SDK.

Usage:
  python plugins/debug/copilot-sdk/auto_programming_task.py \
    --task "Fix failing tests in tests/test_xxx.py" \
    --cwd /Users/fujie/app/python/oui/openwebui-extensions

Notes:
- Default model is gpt-5-mini (low-cost for repeated runs).
- This script DOES NOT pin/upgrade SDK versions.
- Copilot CLI must be available (or set COPILOT_CLI_PATH).
"""

import argparse
import asyncio
import os
import sys
import textwrap
from pathlib import Path
from typing import Optional


DEFAULT_TASK = (
    "Convert plugins/actions/smart-mind-map/smart_mind_map.py (Action plugin) "
    "into a Tool plugin implementation under plugins/tools/. "
    "Keep Copilot SDK version unchanged, follow patterns from "
    "plugins/pipes/github-copilot-sdk/, and implement a runnable MVP with "
    "i18n/status events/basic validation."
)


def _ensure_copilot_importable() -> None:
    """Try local SDK path fallback if `copilot` package is not installed."""
    try:
        import copilot  # noqa: F401

        return
    except Exception:
        pass

    candidates = []

    env_path = os.environ.get("COPILOT_SDK_PYTHON_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path))

    # Default sibling repo path: ../copilot-sdk/python
    # Current file: plugins/debug/copilot-sdk/auto_programming_task.py
    repo_root = Path(__file__).resolve().parents[3]
    candidates.append(repo_root.parent / "copilot-sdk" / "python")

    for path in candidates:
        if path.exists():
            sys.path.insert(0, str(path))
            try:
                import copilot  # noqa: F401

                return
            except Exception:
                continue

    raise RuntimeError(
        "Cannot import `copilot` package. Install copilot-sdk python package "
        "or set COPILOT_SDK_PYTHON_PATH to copilot-sdk/python directory."
    )


def _build_agent_prompt(task: str, cwd: str, extra_context: Optional[str]) -> str:
    extra = extra_context.strip() if extra_context else ""
    return textwrap.dedent(
        f"""
        You are an autonomous coding agent running in workspace: {cwd}

        Primary task:
        {task}

        Requirements:
        1. Inspect relevant files and implement changes directly in the workspace.
        2. Keep changes minimal and focused on the task.
        3. If tests/build commands exist, run targeted validation for changed scope.
        4. If blocked, explain the blocker and propose concrete next steps.
        5. At the end, provide a concise summary of:
           - files changed
           - what was implemented
           - validation results

        {f'Additional context:\n{extra}' if extra else ''}
        """
    ).strip()


def _build_planning_prompt(task: str, cwd: str, extra_context: Optional[str]) -> str:
    extra = extra_context.strip() if extra_context else ""
    return textwrap.dedent(
        f"""
        You are a senior autonomous coding planner running in workspace: {cwd}

        User requirement (may be underspecified):
        {task}

        Goal:
        Expand the requirement into an actionable implementation plan that can be executed end-to-end without extra clarification whenever possible.

        Output format (strict):
        1) Expanded Objective (clear, concrete, scoped)
        2) Assumptions (only necessary assumptions)
        3) Step-by-step Plan (ordered, verifiable)
        4) Validation Plan (how to verify changes)
        5) Execution Brief (concise instruction for implementation agent)

        Constraints:
        - Keep scope minimal and aligned with the user requirement.
        - Do not invent unrelated features.
        - Prefer practical MVP completion.

        {f'Additional context:\n{extra}' if extra else ''}
        """
    ).strip()


def _build_execution_prompt(
    task: str, cwd: str, extra_context: Optional[str], plan_text: str
) -> str:
    extra = extra_context.strip() if extra_context else ""
    return textwrap.dedent(
        f"""
        You are an autonomous coding agent running in workspace: {cwd}

        User requirement:
        {task}

        Planner output (must follow):
        {plan_text}

        Execution requirements:
        1. Execute the plan directly; do not stop after analysis.
        2. If the original requirement is underspecified, use the planner assumptions and continue.
        3. Keep changes minimal, focused, and runnable.
        4. Run targeted validation for changed scope where possible.
        5. If blocked by missing prerequisites, report blocker and the smallest next action.
        6. Finish with concise summary:
           - files changed
           - implemented behavior
           - validation results

        {f'Additional context:\n{extra}' if extra else ''}
        """
    ).strip()


async def _run_single_session(
    client,
    args: argparse.Namespace,
    prompt: str,
    stage_name: str,
    stream_output: bool,
) -> tuple[int, str]:
    from copilot.types import PermissionHandler

    def _auto_user_input_handler(request, _invocation):
        question = ""
        if isinstance(request, dict):
            question = str(request.get("question", "")).lower()
            choices = request.get("choices") or []
            if choices and isinstance(choices, list):
                preferred = args.auto_user_answer.strip()
                for choice in choices:
                    c = str(choice)
                    if preferred and preferred.lower() == c.lower():
                        return {"answer": c, "wasFreeform": False}
                return {"answer": str(choices[0]), "wasFreeform": False}

        preferred = args.auto_user_answer.strip() or "continue"
        if "confirm" in question or "proceed" in question:
            preferred = "yes"
        return {"answer": preferred, "wasFreeform": True}

    session_config = {
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "streaming": True,
        "infinite_sessions": {
            "enabled": True,
        },
        "on_permission_request": PermissionHandler.approve_all,
        "on_user_input_request": _auto_user_input_handler,
    }

    session = await client.create_session(session_config)

    done = asyncio.Event()
    full_messages = []
    has_error = False

    def on_event(event):
        nonlocal has_error
        etype = getattr(event, "type", "unknown")
        if hasattr(etype, "value"):
            etype = etype.value

        if args.trace_events:
            print(f"\n[{stage_name}][EVENT] {etype}", flush=True)

        if etype == "assistant.message_delta" and stream_output:
            delta = getattr(event.data, "delta_content", "") or ""
            if delta:
                print(delta, end="", flush=True)

        elif etype == "assistant.message":
            content = getattr(event.data, "content", "") or ""
            if content:
                full_messages.append(content)

        elif etype == "session.error":
            has_error = True
            done.set()
        elif etype == "session.idle":
            done.set()

    unsubscribe = session.on(on_event)
    heartbeat_task = None

    async def _heartbeat():
        while not done.is_set():
            await asyncio.sleep(max(3, int(args.heartbeat_seconds)))
            if not done.is_set():
                print(
                    f"[{stage_name}][heartbeat] waiting for assistant events...",
                    flush=True,
                )

    try:
        heartbeat_task = asyncio.create_task(_heartbeat())
        await session.send({"prompt": prompt, "mode": "immediate"})
        await asyncio.wait_for(done.wait(), timeout=args.timeout)

        if stream_output:
            print("\n")

        final_message = full_messages[-1] if full_messages else ""
        if final_message:
            print(f"\n===== {stage_name} FINAL MESSAGE =====\n")
            print(final_message)

        if has_error:
            return 1, final_message
        return 0, final_message

    except asyncio.TimeoutError:
        print(f"\n❌ [{stage_name}] Timeout after {args.timeout}s")
        return 124, ""
    except Exception as exc:
        print(f"\n❌ [{stage_name}] Run failed: {exc}")
        return 1, ""
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        try:
            unsubscribe()
        except Exception:
            pass
        try:
            await session.destroy()
        except Exception:
            pass


async def run_task(args: argparse.Namespace) -> int:
    _ensure_copilot_importable()

    from copilot import CopilotClient

    task_text = (args.task or "").strip()
    if args.task_file:
        task_text = Path(args.task_file).read_text(encoding="utf-8").strip()

    if not task_text:
        task_text = DEFAULT_TASK

    direct_prompt = _build_agent_prompt(task_text, args.cwd, args.extra_context)

    client_options = {
        "cwd": args.cwd,
        "log_level": args.log_level,
    }

    if args.cli_path:
        client_options["cli_path"] = args.cli_path

    if args.github_token:
        client_options["github_token"] = args.github_token

    print(f"🚀 Starting Copilot SDK task runner")
    print(f"   cwd: {args.cwd}")
    print(f"   model: {args.model}")
    print(f"   reasoning_effort: {args.reasoning_effort}")
    print(f"   plan_first: {args.plan_first}")

    client = CopilotClient(client_options)
    await client.start()

    try:
        if args.plan_first:
            planning_prompt = _build_planning_prompt(
                task_text, args.cwd, args.extra_context
            )
            print("\n🧭 Stage 1/2: Planning and requirement expansion")
            plan_code, plan_text = await _run_single_session(
                client=client,
                args=args,
                prompt=planning_prompt,
                stage_name="PLANNING",
                stream_output=False,
            )
            if plan_code != 0:
                return plan_code

            execution_prompt = _build_execution_prompt(
                task=task_text,
                cwd=args.cwd,
                extra_context=args.extra_context,
                plan_text=plan_text or "(No planner output provided)",
            )
            print("\n⚙️ Stage 2/2: Execute plan autonomously")
            exec_code, _ = await _run_single_session(
                client=client,
                args=args,
                prompt=execution_prompt,
                stage_name="EXECUTION",
                stream_output=args.stream,
            )
            return exec_code

        print("\n⚙️ Direct mode: Execute task without planning stage")
        exec_code, _ = await _run_single_session(
            client=client,
            args=args,
            prompt=direct_prompt,
            stage_name="EXECUTION",
            stream_output=args.stream,
        )
        return exec_code
    finally:
        try:
            await client.stop()
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run one autonomous programming task with Copilot SDK"
    )
    parser.add_argument(
        "--task",
        default="",
        help="Task description text (if empty, uses built-in default task)",
    )
    parser.add_argument("--task-file", default="", help="Path to a task text file")
    parser.add_argument("--cwd", default=os.getcwd(), help="Workspace directory")
    parser.add_argument(
        "--model",
        default="gpt-5-mini",
        help="Model id for Copilot session (default: gpt-5-mini)",
    )
    parser.add_argument(
        "--reasoning-effort",
        default="medium",
        choices=["low", "medium", "high", "xhigh"],
        help="Reasoning effort",
    )
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout seconds")
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["trace", "debug", "info", "warn", "error"],
        help="Copilot client log level",
    )
    parser.add_argument(
        "--github-token",
        default=os.environ.get("GH_TOKEN", ""),
        help="Optional GitHub token; defaults to GH_TOKEN",
    )
    parser.add_argument(
        "--cli-path",
        default=os.environ.get("COPILOT_CLI_PATH", ""),
        help="Optional Copilot CLI path",
    )
    parser.add_argument(
        "--extra-context",
        default="",
        help="Optional extra context appended to the task prompt",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Print assistant delta stream in real-time",
    )
    parser.add_argument(
        "--trace-events",
        action="store_true",
        help="Print each SDK event type for debugging",
    )
    parser.add_argument(
        "--auto-user-answer",
        default="continue",
        help="Default answer for on_user_input_request",
    )
    parser.add_argument(
        "--heartbeat-seconds",
        type=int,
        default=12,
        help="Heartbeat interval while waiting for events",
    )
    parser.add_argument(
        "--plan-first",
        action="store_true",
        help="Run planning stage before execution (default behavior)",
    )
    parser.add_argument(
        "--no-plan-first",
        action="store_true",
        help="Disable planning stage and run direct execution",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.task_file and (args.task or "").strip():
        parser.error("Use either --task or --task-file, not both")

    args.plan_first = True
    if args.no_plan_first:
        args.plan_first = False
    elif args.plan_first:
        args.plan_first = True

    return asyncio.run(run_task(args))


if __name__ == "__main__":
    raise SystemExit(main())
