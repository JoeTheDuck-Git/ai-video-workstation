#!/bin/bash
# Footage Sifter — contact-sheet builder
# Turns a folder of clips into labelled contact sheets an AI agent can actually inspect
# before judging. This is the eyes of the sift — run it before writing sift.json.
#
# Usage:  bash contactsheet.sh "/path/to/clips"  [clips_per_sheet]
# Output: <clips>/_sheets/sheet_N.jpg   +   a printed clip list (name | duration)
#
# Sampling: 3 frames for clips >=10s, 6 frames for clips <10s (short inserts end on
# an empty frame ON PURPOSE — a sparse sample lies about them, so sample denser).
# Requires: ffmpeg + ffprobe (PATH, or the bundled static-ffmpeg via media_tools.py)
# and ImageMagick (montage). No `montage` (common on Macs without Homebrew)? This
# script hands over to contactsheet_ffmpeg.sh automatically — no install needed.

set -u
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:?usage: bash contactsheet.sh <clips_folder> [clips_per_sheet]}"
PER="${2:-7}"
cd "$DIR" || exit 1

# No ImageMagick → use the ffmpeg-only builder that ships next to this script.
if ! command -v montage >/dev/null 2>&1; then
  echo "(ImageMagick montage not found — using contactsheet_ffmpeg.sh instead)"
  exec bash "$SCRIPT_DIR/contactsheet_ffmpeg.sh" "$PWD"
fi

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

WORK="_sheets/.frames"; mkdir -p "$WORK" _sheets/.strips
echo "=== CLIP LIST (order = filename sort) ==="
printf "%-24s %8s\n" FILE DUR

# sort clips by name for a stable, day-ish order (set -f: names with [ ] * stay literal)
set -f; IFS=$'\n' CLIPS=( $(printf "%s\n" "${CLIPS[@]}" | sort) ); unset IFS; set +f

FAIL=0
for f in "${CLIPS[@]}"; do
  base="${f%.*}"
  dur=$("$FFPROBE_BIN" -v error -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  dur=${dur:-0}
  printf "%-24s %7.1fs\n" "$f" "$dur"
  # dense sampling for short clips
  if awk "BEGIN{exit !($dur < 10)}"; then N=6; else N=3; fi
  frames=()
  for i in $(seq 1 "$N"); do
    pct=$(awk "BEGIN{printf \"%.3f\", ($i-0.5)/$N}")
    t=$(awk "BEGIN{printf \"%.2f\", $dur*$pct}")
    out="$WORK/${base}_$i.jpg"
    "$FFMPEG_BIN" -v error -ss "$t" -i "$f" -frames:v 1 -vf scale=440:-1 "$out" -y 2>/dev/null
    [ -s "$out" ] && frames+=("$out")
  done
  if [ ${#frames[@]} -eq 0 ]; then
    echo "  !! could not read any frame from: $f" >&2; FAIL=$((FAIL+1)); continue
  fi
  if ! montage "${frames[@]}" -tile ${N}x1 -geometry +2+2 -background '#1b1b1b' \
      -fill white -pointsize 22 -title "$base  (${dur%.*}s)" \
      "_sheets/.strips/${base}.jpg"; then
    echo "  !! montage failed for: $f" >&2; FAIL=$((FAIL+1))
  fi
done

# combine per-clip strips into sheets of PER clips each (glob loop: survives spaces)
i=0; sheet=0; batch=()
for s in _sheets/.strips/*.jpg; do
  batch+=("$s"); i=$((i+1))
  if [ $i -ge "$PER" ]; then
    sheet=$((sheet+1))
    montage "${batch[@]}" -tile 1x${PER} -geometry +0+6 -background black "_sheets/sheet_${sheet}.jpg" \
      || { echo "  !! montage failed building sheet_${sheet}.jpg" >&2; FAIL=$((FAIL+1)); }
    batch=(); i=0
  fi
done
if [ ${#batch[@]} -gt 0 ]; then
  sheet=$((sheet+1))
  montage "${batch[@]}" -tile 1x${#batch[@]} -geometry +0+6 -background black "_sheets/sheet_${sheet}.jpg" \
    || { echo "  !! montage failed building sheet_${sheet}.jpg" >&2; FAIL=$((FAIL+1)); }
fi

rm -rf "$WORK" _sheets/.strips 2>/dev/null
echo ""
echo "=== wrote $sheet contact sheet(s) to $DIR/_sheets/ ==="
if [ "$FAIL" -gt 0 ]; then
  echo "!! $FAIL problem(s) above. If montage keeps failing, run: bash \"$SCRIPT_DIR/contactsheet_ffmpeg.sh\" \"$PWD\"" >&2
fi
echo "Now READ every sheet_N.jpg before writing sift.json. Judge on what you SEE."
[ "$FAIL" -eq 0 ]
