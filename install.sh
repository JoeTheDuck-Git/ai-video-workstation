#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATE_DIR="${HOME}/.local/share/ai-video-workstation"
LOCAL_BIN="${HOME}/.local/bin"
NODE_LINK="${STATE_DIR}/node22-current"
ALL_HYPERFRAMES_SKILLS=0

log() { printf '\n==> %s\n' "$*"; }
die() { printf '\nERROR: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'EOF'
Usage: ./install.sh [--all-hyperframes-skills]

  --all-hyperframes-skills  Install every published HyperFrames skill.
                            The default installs/updates the core set.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --all-hyperframes-skills) ALL_HYPERFRAMES_SKILLS=1 ;;
    -h|--help) usage; exit 0 ;;
    *) die "Unknown option: ${arg}" ;;
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

install_dreamina() {
  log "Downloading and running the official Dreamina Canvas installer"
  local temp_script
  temp_script="$(mktemp "${TMPDIR:-/tmp}/dreamina-canvas-install.XXXXXX.sh")"
  curl -fsSL "https://jimeng.jianying.com/canvas-cli/install.sh" -o "$temp_script"
  bash "$temp_script"
  rm -f "$temp_script"
  hash -r
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
  log "Installing bundled Codex skills"
  local skill_name destination
  for skill_name in video-delivery-qc canvas-video-pipeline; do
    destination="${CODEX_HOME:-${HOME}/.codex}/skills/${skill_name}"
    mkdir -p "$destination"
    cp -R "${ROOT_DIR}/skills/${skill_name}/." "$destination/"
    find "$destination" -type d -name __pycache__ -prune -exec rm -rf {} +
  done
}

install_node22
configure_path
node --version
npm --version
install_ffmpeg
install_hyperframes
install_dreamina
install_canvas_video
install_bundled_skills

log "Running availability checks"
"${ROOT_DIR}/scripts/verify.sh"

cat <<'EOF'

Installation finished.

Next:
  1. Open a new terminal, or reload your shell profile.
  2. Run ./scripts/login.sh to authorize Dreamina Canvas.
  3. Run ./scripts/verify.sh again to confirm the login state.
EOF
