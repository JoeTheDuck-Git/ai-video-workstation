#!/usr/bin/env bash
set -uo pipefail

VERIFY_CODEX=1
VERIFY_CLAUDE=1
if [[ "${1:-}" == "--codex-only" ]]; then
  VERIFY_CLAUDE=0
elif [[ "${1:-}" == "--claude-only" ]]; then
  VERIFY_CODEX=0
elif [[ $# -gt 0 ]]; then
  printf 'Usage: %s [--codex-only|--claude-only]\n' "$0" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANAGED_NODE_BIN="${HOME}/.local/share/ai-video-workstation/node22-current/bin"
MANAGED_PYTHON="${HOME}/.local/share/ai-video-workstation/python-venv/bin/python3"
if [[ -x "${MANAGED_NODE_BIN}/node" ]]; then
  export PATH="${MANAGED_NODE_BIN}:${HOME}/.local/bin:${PATH}"
else
  export PATH="${PATH}:${HOME}/.local/bin"
fi
FAILURES=0

ok() { printf 'PASS  %s\n' "$*"; }
warn() { printf 'WARN  %s\n' "$*"; }
fail() { printf 'FAIL  %s\n' "$*"; FAILURES=$((FAILURES + 1)); }

json_top_level_ok() {
  node -e 'let s=""; process.stdin.on("data", d => s += d); process.stdin.on("end", () => { try { process.exit(JSON.parse(s).ok === true ? 0 : 1); } catch { process.exit(1); } });'
}

check_command() {
  if command -v "$1" >/dev/null 2>&1; then
    ok "$1: $(command -v "$1")"
  else
    fail "$1 is not available"
  fi
}

printf 'AI Video Workstation verification\n\n'

check_command node
if command -v node >/dev/null 2>&1; then
  NODE_VERSION="$(node --version 2>/dev/null || true)"
  NODE_MAJOR="${NODE_VERSION#v}"
  NODE_MAJOR="${NODE_MAJOR%%.*}"
  if [[ "$NODE_MAJOR" =~ ^[0-9]+$ ]] && (( NODE_MAJOR >= 22 )); then
    ok "Node.js ${NODE_VERSION}"
  else
    fail "Node.js 22+ is required; found ${NODE_VERSION:-unknown}"
  fi
fi

check_command npm
command -v npm >/dev/null 2>&1 && ok "npm $(npm --version 2>/dev/null || printf unknown)"

check_command ffmpeg
check_command ffprobe
command -v ffmpeg >/dev/null 2>&1 && ok "$(ffmpeg -version 2>/dev/null | head -n 1)"

check_command hyperframes
if command -v hyperframes >/dev/null 2>&1; then
  ok "HyperFrames $(hyperframes --version 2>/dev/null || printf unknown)"
  printf '\n-- HyperFrames doctor --\n'
  DOCTOR_JSON="$(hyperframes doctor --json 2>/dev/null || true)"
  printf '%s\n' "$DOCTOR_JSON"
  if printf '%s' "$DOCTOR_JSON" | json_top_level_ok; then
    ok "HyperFrames doctor"
  else
    warn "HyperFrames doctor reported optional or required items that need attention"
  fi
  printf '\n-- HyperFrames skills --\n'
  hyperframes skills check --json || warn "HyperFrames skills need attention"
fi

check_command canvas-video
if command -v canvas-video >/dev/null 2>&1; then
  printf '\n-- Canvas video runtime --\n'
  CANVAS_DOCTOR="$(canvas-video doctor --json 2>/dev/null || true)"
  printf '%s\n' "$CANVAS_DOCTOR"
  if printf '%s' "$CANVAS_DOCTOR" | json_top_level_ok; then
    ok "canvas-video runtime"
  else
    fail "canvas-video runtime needs attention"
  fi
fi

verify_skills_root() {
  local agent_name="$1" skills_root="$2" qc_script skill_name skill_path tacky_engine
  printf '\n-- %s Skills --\n' "$agent_name"
  qc_script="${skills_root}/video-delivery-qc/scripts/video_qc.py"
  if [[ -f "$qc_script" ]] && [[ -x "$MANAGED_PYTHON" ]] && "$MANAGED_PYTHON" "$qc_script" --help >/dev/null 2>&1; then
    ok "${agent_name}: video-delivery-qc"
  else
    fail "${agent_name}: video-delivery-qc is missing or could not be loaded"
  fi
  for skill_name in canvas-video-pipeline footage-sifter caption-doctor subtitle-translator; do
    skill_path="${skills_root}/${skill_name}/SKILL.md"
    if [[ -f "$skill_path" ]]; then
      ok "${agent_name}: ${skill_name}"
    else
      fail "${agent_name}: ${skill_name} is not installed"
    fi
  done
  tacky_engine="${skills_root}/canvas-video-pipeline/assets/tacky-templates/engine"
  if [[ -f "${tacky_engine}/node_modules/playwright-core/cli.js" ]]; then
    ok "${agent_name}: Tacky Templates isolated renderer"
  else
    fail "${agent_name}: Tacky Templates renderer dependencies are not installed"
  fi
}

[[ "$VERIFY_CODEX" -eq 1 ]] && verify_skills_root "Codex" "${CODEX_HOME:-${HOME}/.codex}/skills"
[[ "$VERIFY_CLAUDE" -eq 1 ]] && verify_skills_root "Claude Code" "${CLAUDE_HOME:-${HOME}/.claude}/skills"

if canvas-video tacky list >/dev/null 2>&1; then
  ok "canvas-video tacky command"
else
  fail "canvas-video tacky command could not resolve an installed Skill"
fi

printf '\n-- Shared subtitle runtime --\n'
if [[ -x "$MANAGED_PYTHON" ]] && "$MANAGED_PYTHON" -c 'import opencc, jieba' >/dev/null 2>&1; then
  ok "subtitle dependencies (opencc, jieba)"
else
  fail "managed subtitle dependencies are missing"
fi

printf '\n'
if (( FAILURES > 0 )); then
  printf 'Verification finished with %d required failure(s).\n' "$FAILURES"
  exit 1
fi
printf 'Verification passed.\n'
