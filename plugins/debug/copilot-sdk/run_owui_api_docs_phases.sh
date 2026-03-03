#!/usr/bin/env bash
# run_owui_api_docs_phases.sh
# One-click runner: generate OpenWebUI API documentation across 8 phases.
#
# Usage:
#   ./plugins/debug/copilot-sdk/run_owui_api_docs_phases.sh
#   ./plugins/debug/copilot-sdk/run_owui_api_docs_phases.sh --start-phase 3
#   ./plugins/debug/copilot-sdk/run_owui_api_docs_phases.sh --only-phase 1
#
# Working directory: /Users/fujie/app/python/oui/open-webui  (open-webui source)
# Task files:        plugins/debug/copilot-sdk/tasks/owui-api-docs/phases/

set -euo pipefail

# ── Resolve paths ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"     # openwebui-extensions root
TASKS_DIR="${SCRIPT_DIR}/tasks/owui-api-docs/phases"
TARGET_CWD="/Users/fujie/app/python/oui/open-webui"   # source repo to scan
RUNNER="${SCRIPT_DIR}/auto_programming_task.py"
PYTHON="${PYTHON:-python3}"

# ── Arguments ────────────────────────────────────────────────────────────────
START_PHASE=1
ONLY_PHASE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --start-phase)
      START_PHASE="$2"; shift 2 ;;
    --only-phase)
      ONLY_PHASE="$2"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# ── Phase definitions ─────────────────────────────────────────────────────────
declare -a PHASE_FILES=(
  "01_route_index.txt"
  "02_auth_users_groups_models.txt"
  "03_chats_channels_memories_notes.txt"
  "04_files_folders_knowledge_retrieval.txt"
  "05_ollama_openai_audio_images.txt"
  "06_tools_functions_pipelines_skills_tasks.txt"
  "07_configs_prompts_evaluations_analytics_scim_utils.txt"
  "08_consolidation_index.txt"
)

declare -a PHASE_LABELS=(
  "Route Index (master table)"
  "Auth / Users / Groups / Models"
  "Chats / Channels / Memories / Notes"
  "Files / Folders / Knowledge / Retrieval"
  "Ollama / OpenAI / Audio / Images"
  "Tools / Functions / Pipelines / Skills / Tasks"
  "Configs / Prompts / Evaluations / Analytics / SCIM / Utils"
  "Consolidation — README + JSON"
)

# ── Pre-flight checks ─────────────────────────────────────────────────────────
echo "============================================================"
echo " OpenWebUI API Docs — Phase Runner"
echo "============================================================"
echo "  Source (--cwd): ${TARGET_CWD}"
echo "  Task files:     ${TASKS_DIR}"
echo "  Runner:         ${RUNNER}"
echo ""

if [[ ! -d "${TARGET_CWD}" ]]; then
  echo "ERROR: Target source directory not found: ${TARGET_CWD}" >&2
  exit 1
fi

if [[ ! -f "${RUNNER}" ]]; then
  echo "ERROR: Runner script not found: ${RUNNER}" >&2
  exit 1
fi

# ── Run phases ────────────────────────────────────────────────────────────────
TOTAL=${#PHASE_FILES[@]}
PASSED=0
FAILED=0

for i in "${!PHASE_FILES[@]}"; do
  PHASE_NUM=$((i + 1))
  TASK_FILE="${TASKS_DIR}/${PHASE_FILES[$i]}"
  LABEL="${PHASE_LABELS[$i]}"

  # --only-phase filter
  if [[ -n "${ONLY_PHASE}" && "${PHASE_NUM}" != "${ONLY_PHASE}" ]]; then
    echo "  [SKIP] Phase ${PHASE_NUM}: ${LABEL}"
    continue
  fi

  # --start-phase filter
  if [[ "${PHASE_NUM}" -lt "${START_PHASE}" ]]; then
    echo "  [SKIP] Phase ${PHASE_NUM}: ${LABEL} (before start phase)"
    continue
  fi

  if [[ ! -f "${TASK_FILE}" ]]; then
    echo "  [ERROR] Task file not found: ${TASK_FILE}" >&2
    FAILED=$((FAILED + 1))
    break
  fi

  echo ""
  echo "──────────────────────────────────────────────────────────"
  echo "  Phase ${PHASE_NUM}/${TOTAL}: ${LABEL}"
  echo "  Task file: ${PHASE_FILES[$i]}"
  echo "──────────────────────────────────────────────────────────"

  if "${PYTHON}" "${RUNNER}" \
      --task-file "${TASK_FILE}" \
      --cwd "${TARGET_CWD}" \
      --model "claude-sonnet-4.6" \
      --reasoning-effort high \
      --no-plan-first; then
    echo "  ✓ Phase ${PHASE_NUM} completed successfully."
    PASSED=$((PASSED + 1))
  else
    EXIT_CODE=$?
    echo ""
    echo "  ✗ Phase ${PHASE_NUM} FAILED (exit code: ${EXIT_CODE})." >&2
    echo "  Fix the issue and re-run with: --start-phase ${PHASE_NUM}" >&2
    FAILED=$((FAILED + 1))
    exit "${EXIT_CODE}"
  fi
done

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Run complete: ${PASSED} passed, ${FAILED} failed"
echo " Output: ${TARGET_CWD}/api_docs/"
echo "============================================================"
