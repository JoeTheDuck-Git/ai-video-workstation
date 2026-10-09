#!/usr/bin/env bash
set -Eeuo pipefail

SOURCE_DIR="${1:-}"
[[ -n "$SOURCE_DIR" ]] || {
  printf 'Usage: %s /path/to/hello-irene-codex\n' "$0" >&2
  exit 2
}

SOURCE_DIR="$(cd "$SOURCE_DIR" 2>/dev/null && pwd)" || {
  printf 'Source directory does not exist: %s\n' "$1" >&2
  exit 1
}

SOURCE_SKILL="${SOURCE_DIR}/skills/beat-cut-editor"
[[ -f "${SOURCE_SKILL}/SKILL.md" ]] || {
  printf 'Missing %s/SKILL.md in source package.\n' "$SOURCE_SKILL" >&2
  exit 1
}

CODEX_SKILLS="${CODEX_HOME:-${HOME}/.codex}/skills"
IRENE_VENV="${HOME}/.irene/venv"
PIP_CACHE="${HOME}/.local/share/ai-video-workstation/pip-cache"
NPM_CACHE="${HOME}/.local/share/ai-video-workstation/npm-cache"
DESTINATION="${CODEX_SKILLS}/beat-cut-editor"

command -v python3 >/dev/null 2>&1 || {
  printf 'Python 3 is required to import beat-cut-editor.\n' >&2
  exit 1
}
MANAGED_NPM="${HOME}/.local/share/ai-video-workstation/node22-current/bin/npm"
if [[ -x "$MANAGED_NPM" ]]; then
  NPM_BIN="$MANAGED_NPM"
else
  NPM_BIN="$(command -v npm || true)"
fi
[[ -n "$NPM_BIN" ]] || {
  printf 'Node.js/npm is required to prepare beat-cut-editor overlays.\n' >&2
  exit 1
}

mkdir -p "$CODEX_SKILLS" "${HOME}/.irene" "$PIP_CACHE" "$NPM_CACHE"
if [[ ! -x "${IRENE_VENV}/bin/python3" ]]; then
  printf 'Creating isolated Irene Python environment: %s\n' "$IRENE_VENV"
  python3 -m venv "$IRENE_VENV"
fi

printf 'Installing beat-cut core dependencies in the isolated Irene environment.\n'
PIP_CACHE_DIR="$PIP_CACHE" "${IRENE_VENV}/bin/python3" -m pip install --disable-pip-version-check \
  'static-ffmpeg>=2.7' 'scenedetect[opencv-headless]>=0.6,<0.7' 'pillow>=10' \
  'numpy>=1.26' 'jieba>=0.42' 'opencc-python-reimplemented>=0.1.7'

timestamp="$(date +%Y%m%d-%H%M%S)"
staging="$(mktemp -d "${TMPDIR:-/tmp}/irene-skill-beat-cut-editor.XXXXXX")"
cleanup() { rm -rf "$staging"; }
trap cleanup EXIT

cp -R "${SOURCE_SKILL}/." "$staging/"
find "$staging" -type d -name node_modules -prune -exec rm -rf {} +
find "$staging" -type d -name __pycache__ -prune -exec rm -rf {} +
find "$staging" -type f -name .DS_Store -delete

if [[ -e "$DESTINATION" ]]; then
  backup="${DESTINATION}.backup-${timestamp}"
  mv "$DESTINATION" "$backup"
  printf 'Backed up existing skill: %s\n' "$backup"
fi
mv "$staging" "$DESTINATION"
trap - EXIT

if [[ -f "${DESTINATION}/scripts/overlay/package-lock.json" ]]; then
  (
    cd "${DESTINATION}/scripts/overlay"
    npm_config_cache="$NPM_CACHE" "$NPM_BIN" ci --no-audit --no-fund
  )
fi

cat <<EOF

Imported beat-cut-editor -> ${DESTINATION}

Core beat editing, IR building, rendering, cards, and audio checks are ready.
Optional features are installed only when requested:
  speech transcription: ${IRENE_VENV}/bin/python3 -m pip install faster-whisper
  custom-song beat analysis: ${IRENE_VENV}/bin/python3 -m pip install librosa

Restart Codex or open a new chat to refresh skill discovery.
EOF
