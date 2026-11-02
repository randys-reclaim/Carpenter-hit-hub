#!/usr/bin/env bash
# Break a reference short into frames for scene planning.
# Usage: tools/breakdown.sh <video.mp4> <out_dir> [clip_seconds]
#
# Produces in <out_dir>:
#   clip_starts/   one full-size frame at the start of each N-second clip (default 8s)
#   every_second/  one frame per second (frame_005s.jpg = 5 seconds in)
#   sheet.jpg      contact sheet at 2 frames/sec, for reading burned-in captions
#   audio.m4a      the original audio track
#   info.txt       duration and size
set -euo pipefail

VIDEO="${1:?usage: breakdown.sh <video> <out_dir> [clip_seconds]}"
OUT="${2:?usage: breakdown.sh <video> <out_dir> [clip_seconds]}"
CLIP="${3:-8}"

mkdir -p "$OUT/clip_starts" "$OUT/every_second"

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$VIDEO")
DUR_INT=${DUR%.*}
SIZE=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 "$VIDEO")
printf 'duration_seconds=%s\nsize=%s\nclip_seconds=%s\n' "$DUR" "$SIZE" "$CLIP" > "$OUT/info.txt"

# One frame per second.
ffmpeg -v error -y -i "$VIDEO" -vf "fps=1" -start_number 0 "$OUT/every_second/frame_%03ds.jpg"

# Frame at the start of each clip window (0.5s in, to skip transition frames).
n=1
for ((t = 0; t < DUR_INT; t += CLIP)); do
  ts=$(awk -v t="$t" 'BEGIN { printf "%.2f", (t == 0 ? 0.5 : t) }')
  ffmpeg -v error -y -ss "$ts" -i "$VIDEO" -frames:v 1 \
    "$OUT/clip_starts/clip$(printf '%02d' "$n")_${t}s.jpg"
  n=$((n + 1))
done

# Contact sheet: 2 fps, 6 columns, small thumbnails.
FRAMES=$(awk -v d="$DUR" 'BEGIN { printf "%d", d * 2 + 1 }')
ROWS=$(( (FRAMES + 5) / 6 ))
ffmpeg -v error -y -i "$VIDEO" -vf "fps=2,scale=240:-1,tile=6x${ROWS}" -frames:v 1 "$OUT/sheet.jpg"

# Audio, if the video has any.
if ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$VIDEO" | grep -q .; then
  ffmpeg -v error -y -i "$VIDEO" -vn -c:a aac -b:a 128k "$OUT/audio.m4a"
fi

echo "Done: $OUT ($(ls "$OUT/clip_starts" | wc -l) clip starts, ${DUR}s)"
