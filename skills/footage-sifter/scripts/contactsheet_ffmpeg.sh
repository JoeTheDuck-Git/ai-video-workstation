#!/bin/bash
# Footage Sifter — contact-sheet builder (ffmpeg-only, no ImageMagick needed)
# Same job as contactsheet.sh but tiles frames with ffmpeg's `tile` filter,
# so it runs on any machine that has ffmpeg/ffprobe alone — or not even that:
# without ffmpeg on PATH it uses the bundled static-ffmpeg via media_tools.py.
#
# Usage:  bash contactsheet_ffmpeg.sh "/path/to/clips"
# Output: <clips>/_sheets/<clipname>.jpg  (one labelled strip per clip)

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:?usage: bash contactsheet_ffmpeg.sh <clips_folder>}"
cd "$DIR" || exit 1

# Prefer the AI Video Workstation Python environment, then fall back to system Python.
PY="python3"
WORKSTATION_VENV="${AI_VIDEO_WORKSTATION_VENV:-$HOME/.local/share/ai-video-workstation/python-venv}"
for cand in "$WORKSTATION_VENV/bin/python3" "$WORKSTATION_VENV/Scripts/python.exe"; do
  [ -x "$cand" ] && { PY="$cand"; break; }
done
FFPROBE_BIN="$(command -v ffprobe || "$PY" "$SCRIPT_DIR/media_tools.py" --ffprobe)" || exit 1
FFMPEG_BIN="$(command -v ffmpeg || "$PY" "$SCRIPT_DIR/media_tools.py" --ffmpeg)" || exit 1

shopt -s nullglob nocaseglob
CLIPS=( *.mov *.mp4 *.m4v *.avi )
shopt -u nocaseglob
[ ${#CLIPS[@]} -eq 0 ] && { echo "no video files in $DIR"; exit 1; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/fs_frames.XXXXXX")"; mkdir -p "$WORK" _sheets
echo "=== CLIP LIST (order = filename sort) ==="
printf "%-26s %8s\n" FILE DUR

set -f; IFS=$'\n' CLIPS=( $(printf "%s\n" "${CLIPS[@]}" | sort) ); unset IFS; set +f

FAIL=0; n=0
for f in "${CLIPS[@]}"; do
  n=$((n+1))
  base="${f%.*}"
  dur=$("$FFPROBE_BIN" -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  dur=${dur:-0}
  printf "%-26s %7.1fs\n" "$f" "$dur"
  if awk "BEGIN{exit !($dur < 10)}"; then N=6; else N=3; fi
  k=0
  for i in $(seq 1 "$N"); do
    pct=$(awk "BEGIN{printf \"%.3f\", ($i-0.5)/$N}")
    t=$(awk "BEGIN{printf \"%.2f\", $dur*$pct}")
    # numbered temp names (not the clip name) so spaces / [ ] in filenames can't break the input pattern
    out="$WORK/c${n}_$(printf '%02d' $((k+1))).jpg"
    "$FFMPEG_BIN" -v error -ss "$t" -i "$f" -frames:v 1 -vf scale=400:-1 "$out" -y 2>/dev/null
    [ -s "$out" ] && k=$((k+1))
  done
  if [ "$k" -eq 0 ]; then
    echo "  !! could not read any frame from: $f" >&2; FAIL=$((FAIL+1)); continue
  fi
  # tile this clip's frames into one horizontal strip using ffmpeg
  "$FFMPEG_BIN" -v error -start_number 1 -i "$WORK/c${n}_%02d.jpg" \
    -filter_complex "tile=${k}x1:margin=4:padding=4:color=0x1b1b1b" \
    -frames:v 1 "_sheets/${base}.jpg" -y \
    || { echo "  !! ffmpeg could not build the strip for: $f" >&2; FAIL=$((FAIL+1)); }
done

rm -rf "$WORK" 2>/dev/null
echo ""
echo "=== wrote strips to $DIR/_sheets/ ==="
ls -1 _sheets/*.jpg 2>/dev/null | wc -l | xargs echo "strips:"
[ "$FAIL" -gt 0 ] && echo "!! $FAIL clip(s) had problems — see messages above." >&2
[ "$FAIL" -eq 0 ]
