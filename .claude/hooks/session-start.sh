#!/bin/bash
# Installs the Higgsfield CLI and its Claude Code skills in cloud sessions.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# Higgsfield CLI (global npm package)
if ! command -v higgsfield >/dev/null 2>&1; then
  npm i -g @higgsfield/cli
fi

# Higgsfield skills for Claude Code (user level, ~/.claude/skills)
if [ ! -d "$HOME/.claude/skills/higgsfield-generate" ]; then
  npx -y skills add higgsfield-ai/skills -g -a claude-code -s '*' -y --copy
fi
