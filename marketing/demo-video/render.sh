#!/bin/sh
# Render every clip prep.py found (landscape + square), copy each clip's .srt next to it, and make the poster.
#   sh marketing/demo-video/render.sh [OUT] [clip ...]     (default OUT: ~/Developer/shotfleet-rc-build/demo-video/out)
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-$HOME/Developer/shotfleet-rc-build/demo-video/out}; [ $# -gt 0 ] && shift
mkdir -p "$OUT"
python3 "$HERE/prep.py"
cd "$HERE/remotion"
[ -d node_modules ] || npm ci
CLIPS=${*:-$(python3 -c "import json;print(' '.join(json.load(open('src/manifest.json'))['clips']))")}
for c in $CLIPS; do
  for v in "$c" "$c-square"; do
    npx remotion render "$v" "$OUT/$v.mp4" --codec=h264 --crf=18 --log=error
  done
  cp "$HERE/clips/$c.srt" "$OUT/$c.srt"
done
# Poster (1280x720): a frame from the iPhone/iPad screenshot grid of clip 3, scaled down.
if python3 -c "import json,sys;sys.exit(0 if 'c3-run-ios' in json.load(open('src/manifest.json'))['clips'] else 1)"; then
  F=$(python3 -c "import json;m=json.load(open('src/manifest.json'));c=m['clips']['c3-run-ios'];print(m['intro']+c['body']+c['gridFrames']-2*m['fade']-5)")
  npx remotion still c3-run-ios "$OUT/poster-1080.png" --frame="$F" --log=error
  ffmpeg -v error -y -i "$OUT/poster-1080.png" -vf scale=1280:720 "$OUT/poster.png" && rm "$OUT/poster-1080.png"
fi
for f in "$OUT"/*.mp4; do
  printf '%s  %s s  %s\n' "$(basename "$f")" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")" "$(du -h "$f" | cut -f1)"
done
python3 "$HERE/web.py" "$OUT"   # web versions + web/manifest.json
