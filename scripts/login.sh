#!/usr/bin/env bash
set -Eeuo pipefail

WITH_HYPERFRAMES=0
if [[ "${1:-}" == "--with-hyperframes" ]]; then
  WITH_HYPERFRAMES=1
elif [[ $# -gt 0 ]]; then
  printf 'Usage: %s [--with-hyperframes]\n' "$0" >&2
  exit 2
fi

MANAGED_NODE_BIN="${HOME}/.local/share/ai-video-workstation/node22-current/bin"
if [[ -x "${MANAGED_NODE_BIN}/node" ]]; then
  export PATH="${MANAGED_NODE_BIN}:${HOME}/.local/bin:${PATH}"
else
  export PATH="${PATH}:${HOME}/.local/bin"
fi

command -v dreamina-canvas >/dev/null 2>&1 || {
  printf 'dreamina-canvas is not installed. Run ./install.sh first.\n' >&2
  exit 1
}

printf 'Starting Dreamina Canvas browser authorization...\n'
dreamina-canvas auth login
dreamina-canvas auth status --format json
dreamina-canvas auth account --format json

if [[ "$WITH_HYPERFRAMES" -eq 1 ]]; then
  command -v hyperframes >/dev/null 2>&1 || {
    printf 'hyperframes is not installed. Run ./install.sh first.\n' >&2
    exit 1
  }
  printf '\nStarting HyperFrames / HeyGen authorization...\n'
  hyperframes auth login
  hyperframes auth status --json
fi

printf '\nAuthorization flow completed. No credentials were copied into this repository.\n'
