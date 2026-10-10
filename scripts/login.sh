#!/usr/bin/env bash
set -Eeuo pipefail

if [[ $# -gt 0 ]]; then
  printf 'Usage: %s\n' "$0" >&2
  exit 2
fi

MANAGED_NODE_BIN="${HOME}/.local/share/ai-video-workstation/node22-current/bin"
if [[ -x "${MANAGED_NODE_BIN}/node" ]]; then
  export PATH="${MANAGED_NODE_BIN}:${HOME}/.local/bin:${PATH}"
else
  export PATH="${PATH}:${HOME}/.local/bin"
fi

command -v hyperframes >/dev/null 2>&1 || {
  printf 'hyperframes is not installed. Run ./install.sh first.\n' >&2
  exit 1
}

printf 'Starting optional HyperFrames / HeyGen authorization...\n'
hyperframes auth login
hyperframes auth status --json

printf '\nAuthorization flow completed. No credentials were copied into this repository.\n'
