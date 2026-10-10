#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${HOME}/.local/share/ai-video-workstation"
LOCAL_BIN="${HOME}/.local/bin"
NODE_LINK="${STATE_DIR}/node22-current"
PYTHON_VENV="${STATE_DIR}/python-venv"
ALL_HYPERFRAMES_SKILLS=0
INSTALL_CODEX=1
INSTALL_CLAUDE=1
INSTALL_TARGET_MODE="both"

log() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: ./install.sh [--all-hyperframes-skills] [--codex-only|--claude-only]

  --all-hyperframes-skills  Install every published HyperFrames skill.
                            The default installs/updates the core set.
  --codex-only              Install bundled Skills only for Codex.
  --claude-only             Install bundled Skills only for Claude Code.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all-hyperframes-skills) ALL_HYPERFRAMES_SKILLS=1; shift ;;
    --codex-only)
      [[ "$INSTALL_TARGET_MODE" != "claude" ]] || die "--codex-only and --claude-only cannot be combined."
      INSTALL_TARGET_MODE="codex"; INSTALL_CODEX=1; INSTALL_CLAUDE=0; shift ;;
    --claude-only)
      [[ "$INSTALL_TARGET_MODE" != "codex" ]] || die "--codex-only and --claude-only cannot be combined."
      INSTALL_TARGET_MODE="claude"; INSTALL_CODEX=0; INSTALL_CLAUDE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: ${1}" ;;
  esac
done

command -v curl >/dev/null 2>&1 || die "curl is required."
command -v tar >/dev/null 2>&1 || die "tar is required."

case "$(uname -s)" in
  Darwin) NODE_PLATFORM="darwin" ;;
  Linux) NODE_PLATFORM="linux" ;;
  *) die "This installer currently supports macOS and Linux." ;;
esac

case "$(uname -m)" in
  arm64|aarch64) NODE_ARCH="arm64" ;;
  x86_64|amd64) NODE_ARCH="x64" ;;
  *) die "Unsupported CPU architecture: $(uname -m)" ;;
esac

mkdir -p "$STATE_DIR" "$LOCAL_BIN"

install_node22() {
  log "Installing the latest Node.js 22 release from nodejs.org"
  local temp_dir checksums archive_name expected actual archive_path extracted_name install_dir
  temp_dir="$(mktemp -d "${TMPDIR:-/tmp}/ai-video-node.XXXXXX")"
  trap 'rm -rf "${temp_dir}"' RETURN
  checksums="${temp_dir}/SHASUMS256.txt"
  curl -fsSL "https://nodejs.org/dist/latest-v22.x/SHASUMS256.txt" -o "$checksums"

  archive_name="$(awk -v stem="-${NODE_PLATFORM}-${NODE_ARCH}.tar.gz" '$2 ~ stem "$" {print $2; exit}' "$checksums")"
  if [[ -z "$archive_name" ]]; then
    archive_name="$(awk -v stem="-${NODE_PLATFORM}-${NODE_ARCH}.tar.xz" '$2 ~ stem "$" {print $2; exit}' "$checksums")"
  fi
  [[ -n "$archive_name" ]] || die "Could not find a Node.js 22 archive for ${NODE_PLATFORM}-${NODE_ARCH}."

  expected="$(awk -v file="$archive_name" '$2 == file {print $1; exit}' "$checksums")"
  archive_path="${temp_dir}/${archive_name}"
  curl -fsSL "https://nodejs.org/dist/latest-v22.x/${archive_name}" -o "$archive_path"

  if command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$archive_path" | awk '{print $1}')"
  elif command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$archive_path" | awk '{print $1}')"
  else
    die "A SHA-256 tool (shasum or sha256sum) is required."
  fi
  [[ "$actual" == "$expected" ]] || die "Node.js archive checksum mismatch."

  extracted_name="${archive_name%.tar.gz}"
  extracted_name="${extracted_name%.tar.xz}"
  install_dir="${STATE_DIR}/${extracted_name}"
  if [[ ! -d "$install_dir" ]]; then
    tar -xf "$archive_path" -C "$temp_dir"
    mv "${temp_dir}/${extracted_name}" "$install_dir"
  fi
  ln -sfn "$install_dir" "$NODE_LINK"
  trap - RETURN
  rm -rf "$temp_dir"
}

configure_path() {
  local shell_file marker_start marker_end
  marker_start="# >>> ai-video-workstation >>>"
  marker_end="# <<< ai-video-workstation <<<"
  if [[ "$NODE_PLATFORM" == "darwin" ]]; then
    shell_file="${HOME}/.zprofile"
  else
    shell_file="${HOME}/.profile"
  fi
  touch "$shell_file"
  if ! grep -Fq "$marker_start" "$shell_file"; then
    {
      printf '\n%s\n' "$marker_start"
      printf 'export PATH="$HOME/.local/share/ai-video-workstation/node22-current/bin:$HOME/.local/bin:$PATH"\n'
      printf '%s\n' "$marker_end"
    } >> "$shell_file"
  fi
  export PATH="${NODE_LINK}/bin:${LOCAL_BIN}:${PATH}"
}

install_ffmpeg() {
  if command -v ffmpeg >/dev/null 2>&1 && command -v ffprobe >/dev/null 2>&1; then
    log "FFmpeg and FFprobe are already available"
    return
  fi

  log "Installing FFmpeg"
  if [[ "$NODE_PLATFORM" == "darwin" ]]; then
    command -v brew >/dev/null 2>&1 || die "Homebrew is required to install FFmpeg on macOS. Install it from https://brew.sh and rerun this script."
    brew install ffmpeg
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y ffmpeg
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y ffmpeg
  elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -S --needed ffmpeg
  else
    die "No supported package manager was found. Install FFmpeg and FFprobe, then rerun."
  fi
}

install_python_tools() {
  if ! command -v python3 >/dev/null 2>&1 || ! python3 -m venv --help >/dev/null 2>&1; then
    log "Installing Python 3 and venv support"
    if [[ "$NODE_PLATFORM" == "darwin" ]]; then
      command -v brew >/dev/null 2>&1 || die "Homebrew is required to install Python on macOS. Install it from https://brew.sh and rerun this script."
      brew install python@3.12
    elif command -v apt-get >/dev/null 2>&1; then
      sudo apt-get update
      sudo apt-get install -y python3 python3-venv
    elif command -v dnf >/dev/null 2>&1; then
      sudo dnf install -y python3
    elif command -v pacman >/dev/null 2>&1; then
      sudo pacman -S --needed python
    else
      die "No supported package manager was found. Install Python 3 with venv support, then rerun."
    fi
  fi
  command -v python3 >/dev/null 2>&1 || die "Python 3 is required."
  if [[ ! -x "${PYTHON_VENV}/bin/python3" ]]; then
    log "Creating the isolated AI Video Workstation Python environment"
    python3 -m venv "$PYTHON_VENV"
  fi
  log "Installing subtitle dependencies"
  "${PYTHON_VENV}/bin/python3" -m pip install --disable-pip-version-check \
    'opencc-python-reimplemented>=0.1.7' 'jieba>=0.42'
}

install_hyperframes() {
  log "Installing HyperFrames CLI"
  npm install -g --prefix "$HOME/.local" hyperframes@latest
  hash -r
  if [[ "$ALL_HYPERFRAMES_SKILLS" -eq 1 ]]; then
    log "Installing the complete published HyperFrames skill set"
    hyperframes skills
  else
    log "Installing/updating the HyperFrames core skill set"
    hyperframes skills update
  fi
}

install_canvas_video() {
  log "Installing isolated canvas-video runtime"
  local destination
  destination="${STATE_DIR}/canvas-video"
  mkdir -p "$destination"
  cp -R "${ROOT_DIR}/runtime/canvas-video/." "$destination/"
  chmod +x "${destination}/bin/canvas-video.mjs"
  npm ci --prefix "$destination" --no-audit --no-fund
  "${destination}/node_modules/.bin/playwright" install chromium
  ln -sfn "${destination}/bin/canvas-video.mjs" "${LOCAL_BIN}/canvas-video"
}

install_bundled_skills() {
  local skill_name destination skills_root agent_name tacky_engine
  local -a targets=()
  [[ "$INSTALL_CODEX" -eq 1 ]] && targets+=("Codex|${CODEX_HOME:-${HOME}/.codex}/skills")
  [[ "$INSTALL_CLAUDE" -eq 1 ]] && targets+=("Claude Code|${CLAUDE_HOME:-${HOME}/.claude}/skills")

  for target in "${targets[@]}"; do
    agent_name="${target%%|*}"
    skills_root="${target#*|}"
    log "Installing bundled Skills for ${agent_name}"
    mkdir -p "$skills_root"
    for skill_name in video-delivery-qc canvas-video-pipeline footage-sifter caption-doctor subtitle-translator; do
      destination="${skills_root}/${skill_name}"
      mkdir -p "$destination"
      cp -R "${ROOT_DIR}/skills/${skill_name}/." "$destination/"
      find "$destination" -type d -name __pycache__ -prune -exec rm -rf {} +
    done

    tacky_engine="${skills_root}/canvas-video-pipeline/assets/tacky-templates/engine"
    if [[ -f "${tacky_engine}/package-lock.json" ]]; then
      log "Preparing the isolated Tacky Templates renderer for ${agent_name}"
      (
        cd "$tacky_engine"
        npm ci --no-audit --no-fund
        ./node_modules/.bin/playwright-core install chromium
      )
    fi
  done
}

install_node22
configure_path
node --version
npm --version
install_ffmpeg
install_python_tools
install_hyperframes
install_canvas_video
install_bundled_skills

log "Running availability checks"
VERIFY_ARGS=()
[[ "$INSTALL_CODEX" -eq 1 && "$INSTALL_CLAUDE" -eq 0 ]] && VERIFY_ARGS+=(--codex-only)
[[ "$INSTALL_CODEX" -eq 0 && "$INSTALL_CLAUDE" -eq 1 ]] && VERIFY_ARGS+=(--claude-only)
"${ROOT_DIR}/scripts/verify.sh" "${VERIFY_ARGS[@]}"

cat <<'EOF'

Installation finished.

Next:
  1. Open a new terminal, or reload your shell profile, then restart the installed AI coding app(s).
  2. Run ./scripts/verify.sh to check the local video toolchain.
  3. Optional: run ./scripts/login.sh only if you need HyperFrames / HeyGen cloud features.
EOF
