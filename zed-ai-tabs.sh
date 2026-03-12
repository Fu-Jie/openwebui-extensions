#!/bin/bash
# ==============================================================================
# ai-tabs - Ultra Orchestrator
# Version: v1.0.0
# License: MIT
# Author: Fu-Jie
# Description: Batch-launches and orchestrates multiple AI CLI tools as Tabs.
# ==============================================================================

# 1. Single-Instance Lock
LOCK_FILE="/tmp/ai_terminal_launch.lock"
# If lock is less than 10 seconds old, another instance is running. Exit.
if [ -f "$LOCK_FILE" ]; then
    LOCK_TIME=$(stat -f %m "$LOCK_FILE")
    NOW=$(date +%s)
    if (( NOW - LOCK_TIME < 10 )); then
        echo "⚠️ Another launch in progress. Skipping to prevent duplicates."
        exit 0
    fi
fi
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"' EXIT

# 2. Configuration & Constants
INIT_DELAY=4.5
PASTE_DELAY=0.3
CMD_CREATION_DELAY=0.3
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

# Search for .env
if [ -f "${SCRIPT_DIR}/.env" ]; then
    ENV_FILE="${SCRIPT_DIR}/.env"
elif [ -f "${PARENT_DIR}/.env" ]; then
    ENV_FILE="${PARENT_DIR}/.env"
fi

# Supported Tools
SUPPORTED_TOOLS=(
    "claude:--continue"
    "opencode:--continue"
    "gemini:--resume latest"
    "copilot:--continue"
    "iflow:--continue"
    "kilo:--continue"
)

FOUND_TOOLS_NAMES=()
FOUND_CMDS=()

# 3. Part A: Load Manual Configuration
if [ -f "$ENV_FILE" ]; then
    set -a; source "$ENV_FILE"; set +a
    for var in $(compgen -v | grep '^TOOL_[0-9]' | sort -V); do
        TPATH="${!var}"
        if [ -x "$TPATH" ]; then
            NAME=$(basename "$TPATH")
            FLAG="--continue"
            for item in "${SUPPORTED_TOOLS[@]}"; do
                [[ "${item%%:*}" == "$NAME" ]] && FLAG="${item#*:}" && break
            done
            FOUND_TOOLS_NAMES+=("$NAME")
            FOUND_CMDS+=("'$TPATH' $FLAG || '$TPATH' || exec \$SHELL")
        fi
    done
fi

# 4. Part B: Automatic Tool Discovery
for item in "${SUPPORTED_TOOLS[@]}"; do
    NAME="${item%%:*}"
    FLAG="${item#*:}"
    ALREADY_CONFIGURED=false
    for configured in "${FOUND_TOOLS_NAMES[@]}"; do
        [[ "$configured" == "$NAME" ]] && ALREADY_CONFIGURED=true && break
    done
    [[ "$ALREADY_CONFIGURED" == true ]] && continue
    TPATH=$(which "$NAME" 2>/dev/null)
    if [ -z "$TPATH" ]; then
        SEARCH_PATHS=(
            "/opt/homebrew/bin/$NAME"
            "/usr/local/bin/$NAME"
            "$HOME/.local/bin/$NAME"
            "$HOME/bin/$NAME"
            "$HOME/.$NAME/bin/$NAME"
            "$HOME/.nvm/versions/node/*/bin/$NAME"
            "$HOME/.npm-global/bin/$NAME"
            "$HOME/.cargo/bin/$NAME"
        )
        for p in "${SEARCH_PATHS[@]}"; do
            for found_p in $p; do [[ -x "$found_p" ]] && TPATH="$found_p" && break 2; done
        done
    fi
    if [ -n "$TPATH" ]; then
        FOUND_TOOLS_NAMES+=("$NAME")
        FOUND_CMDS+=("'$TPATH' $FLAG || '$TPATH' || exec \$SHELL")
    fi
done

NUM_FOUND=${#FOUND_CMDS[@]}
[[ "$NUM_FOUND" -eq 0 ]] && exit 1

# 5. Core Orchestration (Reset + Launch)
# Using Command Palette automation to avoid the need for manual shortcut binding.
AS_SCRIPT="tell application \"System Events\"\n"

# Phase A: Creation (Using Command Palette to ensure it opens in Editor Area)
for ((i=1; i<=NUM_FOUND; i++)); do
    AS_SCRIPT+="    keystroke \"p\" using {command down, shift down}\n"
    AS_SCRIPT+="    delay 0.1\n"
    # Ensure we are searching for the command. Using clipboard for speed and universal language support.
    AS_SCRIPT+="    set the clipboard to \"workspace: new center terminal\"\n"
    AS_SCRIPT+="    keystroke \"v\" using {command down}\n"
    AS_SCRIPT+="    delay 0.1\n"
    AS_SCRIPT+="    keystroke return\n"
    AS_SCRIPT+="    delay $CMD_CREATION_DELAY\n"
done

# Phase B: Warmup
AS_SCRIPT+="    delay $INIT_DELAY\n"

# Phase C: Command Injection (Reverse)
for ((i=NUM_FOUND-1; i>=0; i--)); do
    FULL_CMD="${FOUND_CMDS[$i]}"
    CLEAN_CMD=$(echo "$FULL_CMD" | sed 's/"/\\"/g')
    AS_SCRIPT+="    set the clipboard to \"$CLEAN_CMD\"\n"
    AS_SCRIPT+="    delay 0.1\n"
    AS_SCRIPT+="    keystroke \"v\" using {command down}\n"
    AS_SCRIPT+="    delay $PASTE_DELAY\n"
    AS_SCRIPT+="    keystroke return\n"
    if [ $i -gt 0 ]; then
        AS_SCRIPT+="    delay 0.5\n"
        AS_SCRIPT+="    keystroke \"[\" using {command down, shift down}\n"
    fi
done
AS_SCRIPT+="end tell"

# Execute
echo -e "$AS_SCRIPT" | osascript
echo "✨ Ai tabs initialized successfully ($NUM_FOUND tools found)."
