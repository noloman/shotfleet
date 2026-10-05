#!/bin/bash
# Regenerates ../shotfleet-product.mp4 and ../poster.png. PRICE=0 bash build.sh leaves out the price line.
set -euo pipefail
cd "$(dirname "$0")"
python3 build.py
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt:format=duration,size -of default=nw=1 ../shotfleet-product.mp4
