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

CODEX_SKILLS="${CODEX_HOME:-${HOME}/.codex}/skills"
IRENE_VENV="${HOME}/.irene/venv"
PIP_CACHE="${HOME}/.local/share/ai-video-workstation/pip-cache"
SKILLS=(footage-sifter caption-doctor subtitle-translator)

for skill_name in "${SKILLS[@]}"; do
  source_skill="${SOURCE_DIR}/skills/${skill_name}"
  [[ -f "${source_skill}/SKILL.md" ]] || {
    printf 'Missing %s/SKILL.md in source package.\n' "$source_skill" >&2
    exit 1
  }
done

command -v python3 >/dev/null 2>&1 || {
  printf 'Python 3 is required to import the Irene skills.\n' >&2
  exit 1
}

mkdir -p "$CODEX_SKILLS" "${HOME}/.irene" "$PIP_CACHE"
if [[ ! -x "${IRENE_VENV}/bin/python3" ]]; then
  printf 'Creating isolated Irene Python environment: %s\n' "$IRENE_VENV"
  python3 -m venv "$IRENE_VENV"
fi

PIP_CACHE_DIR="$PIP_CACHE" "${IRENE_VENV}/bin/python3" -m pip install --disable-pip-version-check \
  'opencc-python-reimplemented>=0.1.7' 'jieba>=0.42'

timestamp="$(date +%Y%m%d-%H%M%S)"
for skill_name in "${SKILLS[@]}"; do
  source_skill="${SOURCE_DIR}/skills/${skill_name}"
  destination="${CODEX_SKILLS}/${skill_name}"
  staging="$(mktemp -d "${TMPDIR:-/tmp}/irene-skill-${skill_name}.XXXXXX")"
  cp -R "${source_skill}/." "$staging/"
  find "$staging" -type d -name __pycache__ -prune -exec rm -rf {} +
  find "$staging" -type f -name .DS_Store -delete
  if [[ -e "$destination" ]]; then
    backup="${destination}.backup-${timestamp}"
    mv "$destination" "$backup"
    printf 'Backed up existing skill: %s\n' "$backup"
  fi
  mv "$staging" "$destination"
  printf 'Imported %s -> %s\n' "$skill_name" "$destination"
done

printf '\nImported 3 Irene capability skills. Restart Codex or open a new chat to refresh skill discovery.\n'
