#!/usr/bin/env python3
import argparse
import asyncio
import datetime as dt
import json
import logging
import os
import sys
import textwrap
from typing import Iterable, List, Optional

from copilot import CopilotClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("copilot_sdk_guide")

DEFAULT_CONTEXT_URLS = [
    "https://raw.githubusercontent.com/github/copilot-sdk/main/README.md",
    "https://raw.githubusercontent.com/github/copilot-sdk/main/python/README.md",
    "https://raw.githubusercontent.com/github/copilot-sdk/main/docs/getting-started.md",
    "https://raw.githubusercontent.com/github/copilot-cli/main/README.md",
    "https://raw.githubusercontent.com/github/copilot-cli/main/changelog.md",
    "https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli",
    "https://docs.github.com/en/copilot/concepts/agents/about-agent-skills",
    "https://raw.githubusercontent.com/github/awesome-copilot/main/README.md",
    "https://raw.githubusercontent.com/github/awesome-copilot/main/skills/copilot-sdk/SKILL.md",
    "https://raw.githubusercontent.com/github/awesome-copilot/main/instructions/agent-skills.instructions.md",
]

AWESOME_COPILOT_REPO = "github/awesome-copilot"
AWESOME_COPILOT_BRANCH = "main"
AWESOME_COPILOT_DOC_DIRS = ["docs/", "instructions/"]

TOPICS = [
    "MCP Server Integration: JSON-RPC config and SDK hooks",
    "Agent Manifests: Defining capabilities and permissions programmatically",
    "Headless Auth: Device Code Flow and credential persistence",
    "Session Replay vs Resume: Handling stateless frontend history",
    "Advanced Session Hooks: Intercepting and modifying user prompts",
    "Workspace Virtualization: Handling CWD for remote/virtual files",
    "Error Recovery: Handling session disconnects and re-auth",
    "Confirmation Events: programmatic handling of 'confirmation_required'",
    "Skills: Conflict resolution and precedence defaults",
    "Debugging: Tracing JSON-RPC traffic in the SDK",
    "Billing & Policies: How seat management affects SDK features",
]

QUESTION_TEMPLATES = [
    "Give a concise overview of {topic}.",
    "Provide best practices and common pitfalls for {topic}.",
    "Show a minimal example snippet for {topic}.",
    "List recommended configuration defaults for {topic}.",
    "How does {topic} relate to building a custom Agent?",
]

CLI_FOCUS_QUESTIONS = [
    "How to configure MCP servers in ~/.copilot/config.json for SDK usage?",
    "What CLI environment variables force 'Agent' mode vs 'Generic' mode?",
    "Explain the 'confirmation' flow in CLI and how it maps to SDK events.",
    "Does the CLI support 'dry-run' permission checks for tools?",
    "What are the undocumented requirements for 'workspace' context updates?",
    "How does the CLI handle 'device code' re-authentication automatically?",
]


def build_questions(max_questions: int) -> List[str]:
    questions: List[str] = []

    for topic in TOPICS:
        for template in QUESTION_TEMPLATES:
            questions.append(template.format(topic=topic))

    questions.extend(CLI_FOCUS_QUESTIONS)

    # De-duplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for q in questions:
        if q in seen:
            continue
        seen.add(q)
        uniq.append(q)

    return uniq[:max_questions]


def build_deep_dive_prompts() -> List[str]:
    return [
        "Provide a python code example for configuring `CopilotClient` to connect to a local MCP server (e.g. Brave Search) via `CopilotClient` config.",
        "Explain how to programmatically handle `tool.confirmation_required` events in a non-interactive stream using `session.on()`.",
        "Show how to implement a 'Device Flow' login helper using SDK primitives (if available) or raw HTTP showing how to persist credentials.",
        "Compare the pros and cons of 'Session Replay' (fast-forwarding history) vs 'Session Resume' (stateful ID) for a stateless web backend like OpenWebUI.",
        "Detail the exact protocol for 'Virtual Workspace': how to implement a file system provider that feeds content to Copilot without physical files.",
        "Create an 'Agent Manifest' example: how to define an Agent capable of specific high-privileged tools via SDK.",
        "List all 'hidden' `SessionConfig` parameters relevant to Agent behavior and personality.",
    ]


def load_questions(path: str) -> List[str]:
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
        raise ValueError("JSON must be an array of strings")

    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    return [line for line in lines if line]


def fetch_url(url: str, headers: Optional[dict] = None) -> str:
    import urllib.request
    import time

    retries = 3
    if headers is None:
        headers = {}

    req = urllib.request.Request(url, headers=headers)

    for i in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:
            if i == retries - 1:
                logger.warning(
                    "Failed to fetch %s after %d attempts: %s", url, retries, exc
                )
                return ""
            time.sleep(1 * (i + 1))
    return ""


def list_repo_markdown_urls(
    repo: str,
    branch: str,
    dir_prefixes: List[str],
) -> List[str]:
    api_url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
    headers = {}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.environ.get('GITHUB_TOKEN')}"

    try:
        content = fetch_url(api_url, headers=headers)
        if not content:
            return []
        data = json.loads(content)
    except Exception as exc:
        logger.warning("Failed to list repo tree: %s", exc)
        return []

    tree = data.get("tree", []) if isinstance(data, dict) else []
    urls: List[str] = []
    for item in tree:
        if not isinstance(item, dict):
            continue
        path = item.get("path", "")
        if not path or not path.endswith(".md"):
            continue
        if any(path.startswith(prefix) for prefix in dir_prefixes):
            raw = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"
            urls.append(raw)
    return urls


def read_local_sdk_source(max_chars: int = 300000) -> str:
    """
    Locates the installed 'copilot' package and reads its source code.
    This ensures analysis is based on the actual installed version, not just docs.
    """
    try:
        import copilot
    except ImportError:
        logger.error("Could not import 'copilot' SDK. Is it installed?")
        return ""

    package_dir = os.path.dirname(copilot.__file__)
    logger.info(f"Reading SDK source from: {package_dir}")

    source_chunks = []
    total_chars = 0

    # Prioritize key files that define core logic
    priority_files = ["client.py", "session.py", "types.py", "events.py", "__init__.py"]

    # First pass: Recursively find all .py files
    all_py_files = []
    for root, dirs, files in os.walk(package_dir):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                all_py_files.append(os.path.join(root, file))

    # Sort files: priority files first, then alphabetical
    def sort_key(path):
        fname = os.path.basename(path)
        if fname in priority_files:
            return (0, priority_files.index(fname))
        return (1, path)

    all_py_files.sort(key=sort_key)

    for path in all_py_files:
        rel_path = os.path.relpath(path, os.path.dirname(package_dir))
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            # Add file delimiter for the model
            header = f"\n\n# ==================================================\n# SOURCE CODE FILE: {rel_path}\n# ==================================================\n"
            chunk = header + content

            if total_chars + len(chunk) > max_chars:
                remaining = max_chars - total_chars
                if remaining > len(header) + 100:
                    source_chunks.append(
                        chunk[:remaining] + "\n# [TRUNCATED DUE TO LENGTH LIMIT]"
                    )
                logger.warning(f"Context limit reached. Stopping at {rel_path}")
                break

            source_chunks.append(chunk)
            total_chars += len(chunk)
            logger.info(f"Loaded source file: {rel_path} ({len(content)} chars)")

        except Exception as e:
            logger.warning(f"Failed to read source file {path}: {e}")

    return "".join(source_chunks)


def build_context(urls: Iterable[str], max_chars: int) -> str:
    chunks: List[str] = []
    remaining = max_chars

    for url in urls:
        if remaining <= 0:
            break
        try:
            content = fetch_url(url)
            header = f"[Source: {url}]\n"
            if len(header) >= remaining:
                break
            remaining -= len(header)

            if len(content) > remaining:
                content = content[:remaining] + "\n[TRUNCATED]\n"
                remaining = 0
            else:
                remaining -= len(content)

            chunks.append(header + content)
            logger.info("Fetched context: %s", url)
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", url, exc)

    return "\n\n".join(chunks)


def write_jsonl(path: str, item: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def write_markdown_header(path: str, title: str, meta: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        for k, v in meta.items():
            f.write(f"- **{k}**: {v}\n")
        f.write("\n---\n\n")


def append_markdown_qa(path: str, question: str, answer: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"## Q: {question}\n\n")
        f.write(f"{answer}\n\n")


def clamp_questions(questions: List[str], max_questions: int) -> List[str]:
    return questions[: max(1, min(max_questions, 400))]


def print_progress_bar(
    iteration,
    total,
    prefix="",
    suffix="",
    decimals=1,
    length=50,
    fill="█",
    printEnd="\r",
):
    """
    Call in a loop to create terminal progress bar
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + "-" * (length - filledLength)
    # Clear line extension to handle shrinking suffixes
    print(f"\r{prefix} |{bar}| {percent}% {suffix}\033[K", end=printEnd)
    # Print New Line on Complete
    if iteration == total:
        print()


async def run_session(
    model: str,
    questions: List[str],
    output_dir: str,
    context: str,
    session_id: Optional[str],
    delay: float,
    output_lang: str,
    enable_infinite_sessions: bool,
    timeout: int,
) -> None:
    client = CopilotClient()
    await client.start()

    session_config = {"model": model}
    if session_id:
        session_config["session_id"] = session_id
    if enable_infinite_sessions:
        session_config["infinite_sessions"] = {
            "enabled": True,
            "background_compaction_threshold": 0.8,
            "buffer_exhaustion_threshold": 0.95,
        }

    session = await client.create_session(session_config)

    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    jsonl_path = os.path.join(output_dir, f"copilot_sdk_guide_{timestamp}.jsonl")
    md_path = os.path.join(output_dir, f"copilot_sdk_guide_{timestamp}.md")

    write_markdown_header(
        md_path,
        "GitHub Copilot SDK & CLI 研究报告",
        {
            "model": model,
            "questions": len(questions),
            "timestamp": timestamp,
            "language": output_lang,
        },
    )

    lang_instruction = "Chinese" if "zh" in output_lang.lower() else "English"

    system_prompt = textwrap.dedent(
        f"""
        You are an expert assistant. Focus on GitHub Copilot SDK and GitHub Copilot CLI.
        
        CRITICAL INSTRUCTION: SOURCE CODE FIRST.
        You have been provided with the ACTUAL PYTHON SOURCE CODE of the `copilot` SDK in the context.
        When answering questions:
        1. FIRST, analyze the provided source code (look for class definitions, type hints, methods).
        2. THEN, refer to documentation if source code is ambiguous.
        3. Do NOT hallucinate methods that do not exist in the source code.
        4. If a feature (like MCP) is not explicitly in the code, explain how to implement it using the available primitives (low-level hooks/events).

        Provide accurate, concise answers in {lang_instruction}. When relevant, include command names,
        configuration keys, and pitfalls. Use bullet points where useful.

        Output requirements:
        - Write in {lang_instruction}.
        - Provide practical code snippets (Python/TypeScript/CLI) when helpful.
        - Include a short "建议/落地" section for integration into a pipe.
        - If citing facts from provided context, briefly mention the source URL.
        """
    ).strip()

    if context:
        system_prompt += "\n\nAdditional context:\n" + context

    await session.send_and_wait({"prompt": system_prompt}, timeout=timeout)

    total_q = len(questions)
    print_progress_bar(0, total_q, prefix="Progress:", suffix="Starting...", length=30)

    for idx, question in enumerate(questions, start=1):
        # Update progress bar (Asking...)
        q_short = (question[:40] + "...") if len(question) > 40 else question.ljust(43)
        print_progress_bar(
            idx - 1, total_q, prefix="Progress:", suffix=f"Asking: {q_short}", length=30
        )

        # Log to file/debug only
        logger.debug("[%s/%s] Asking: %s", idx, total_q, question)

        answer = ""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await session.send_and_wait(
                    {"prompt": question}, timeout=timeout
                )
                answer = response.data.content if response and response.data else ""
                break
            except Exception as e:
                logger.error(
                    f"Error asking question (Attempt {attempt+1}/{max_retries}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    answer = f"Error retrieving answer: {e}"

        write_jsonl(
            jsonl_path,
            {
                "index": idx,
                "question": question,
                "answer": answer,
                "model": model,
            },
        )
        append_markdown_qa(md_path, question, answer)

        # Update progress bar (Done...)
        print_progress_bar(
            idx, total_q, prefix="Progress:", suffix=f"Done: {q_short}", length=30
        )

        if delay > 0:
            await asyncio.sleep(delay)

    await session.destroy()
    await client.stop()

    logger.info("Saved output to %s and %s", jsonl_path, md_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask up to 100 Copilot SDK questions via GitHub Copilot SDK",
    )
    parser.add_argument("--model", default="gpt-5.2-codex", help="Model to use")
    parser.add_argument(
        "--max-questions",
        type=int,
        default=100,
        help="Max number of questions (1-400)",
    )
    parser.add_argument(
        "--questions-file",
        default="",
        help="Path to .txt or .json list of questions",
    )
    parser.add_argument(
        "--context-url",
        action="append",
        default=[],
        help="Additional context URL (repeatable)",
    )
    parser.add_argument(
        "--no-default-context",
        action="store_true",
        help="Disable default Copilot SDK context URLs",
    )
    parser.add_argument(
        "--include-awesome-copilot-docs",
        action="store_true",
        help="Include all markdown files from awesome-copilot/docs",
    )
    parser.add_argument(
        "--include-awesome-copilot-instructions",
        action="store_true",
        help="Include all markdown files from awesome-copilot/instructions",
    )
    parser.add_argument(
        "--no-sdk-source",
        action="store_true",
        help="Do NOT read local SDK source code (default: reads source)",
    )
    parser.add_argument(
        "--session-id",
        default="",
        help="Optional custom session ID",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Directory to save outputs",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between questions (seconds)",
    )
    parser.add_argument(
        "--max-context-chars",
        type=int,
        default=400000,
        help="Max characters of aggregated context (default: 400000)",
    )
    parser.add_argument(
        "--disable-infinite-sessions",
        action="store_true",
        help="Disable infinite sessions (default: enabled)",
    )
    parser.add_argument(
        "--output-lang",
        default="zh-CN",
        help="Output language (default: zh-CN)",
    )
    parser.add_argument(
        "--deep-dive",
        action="store_true",
        help="Append deep-dive prompts for more detailed research",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3600,
        help="Session request timeout in seconds (default: 3600)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.questions_file:
        questions = load_questions(args.questions_file)
    else:
        # Generate enough questions to cover everything
        questions = build_questions(9999)

    if args.deep_dive:
        # Prepend deep dive questions to ensure they are prioritized
        questions = build_deep_dive_prompts() + questions

    questions = clamp_questions(questions, args.max_questions)
    if not questions:
        logger.error("No questions to ask")
        sys.exit(1)

    context_urls = [] if args.no_default_context else list(DEFAULT_CONTEXT_URLS)

    if args.include_awesome_copilot_docs:
        context_urls.extend(
            list_repo_markdown_urls(
                AWESOME_COPILOT_REPO,
                AWESOME_COPILOT_BRANCH,
                ["docs/"],
            )
        )

    if args.include_awesome_copilot_instructions:
        context_urls.extend(
            list_repo_markdown_urls(
                AWESOME_COPILOT_REPO,
                AWESOME_COPILOT_BRANCH,
                ["instructions/"],
            )
        )

    context_urls.extend(args.context_url or [])

    # 1. Read local source code first (Priority: High)
    # We allocate up to max_context_chars to source code initially.
    # The actual usage will likely be less for a typical SDK.
    source_context = ""
    source_chars_count = 0
    if not args.no_sdk_source:
        source_context = read_local_sdk_source(args.max_context_chars)
        source_chars_count = len(source_context)
        logger.info(f"Source context usage: {source_chars_count} chars")

    # 2. Calculate remaining budget for Web Docs (Priority: Secondary)
    # We ensure we don't exceed the global limit.
    remaining_chars = max(10000, args.max_context_chars - source_chars_count)
    logger.info(f"Remaining budget for web docs: {remaining_chars} chars")

    # 3. Fetch remote docs
    web_context = build_context(context_urls, remaining_chars)

    combined_context = ""
    # Assemble context in order of authority (Source > Docs)
    if source_context:
        combined_context += (
            "# PRIMARY SOURCE: LOCAL SDK CODE (AUTHORITATIVE)\n"
            + source_context
            + "\n\n"
        )
    if web_context:
        combined_context += (
            "# SECONDARY SOURCE: WEB DOCUMENTATION & AWESOME-COPILOT\n" + web_context
        )

    output_dir = args.output_dir or os.path.join(
        os.getcwd(), "plugins", "debug", "copilot_sdk_research", "outputs"
    )
    os.makedirs(output_dir, exist_ok=True)

    asyncio.run(
        run_session(
            model=args.model,
            questions=questions,
            output_dir=output_dir,
            context=combined_context,
            session_id=args.session_id or None,
            delay=args.delay,
            output_lang=args.output_lang,
            enable_infinite_sessions=not args.disable_infinite_sessions,
            timeout=args.timeout,
        )
    )


if __name__ == "__main__":
    main()
