#!/bin/sh
# Prepare the demo session folder the tapes run in (no devices are touched):
#   SESSION/bin/shotfleet    runs this checkout's shotfleet.py (the recording uses the source, not an installed copy)
#   SESSION/rc               sourced (hidden) by every tape: PATH, a plain "$ " prompt, cd myapp
#   SESSION/myapp/build/     the fixture apps, built from tools/fixture-app and tools/fixture-app-android
#   SESSION/edits/           the config and flow clip 2 copies in after `shotfleet init`
#   SESSION/myapp/.github/workflows/screenshots.yml   the CI recipe, copied verbatim from site/public/docs.html
# Usage: sh marketing/demo-video/session.sh [SESSION]   (default: ~/Developer/shotfleet-rc-build/demo-video/session)
# It wipes SESSION/myapp first (a fresh project each time).
set -eu
REPO=$(cd "$(dirname "$0")/../.." && pwd)
S=${1:-$HOME/Developer/shotfleet-rc-build/demo-video/session}
mkdir -p "$S/bin" "$S/edits" "$S/rec"; ln -sfn "$REPO/marketing/demo-video/tapes" "$S/tapes"
rm -rf "$S/myapp"; mkdir -p "$S/myapp/build" "$S/myapp/.github/workflows"
sh "$REPO/tools/fixture-app/build.sh" "$S/myapp/build" >/dev/null 2>&1
sh "$REPO/tools/fixture-app-android/build.sh" "$S/myapp/build" >/dev/null
rm -f "$S/myapp/build"/*.keystore "$S/myapp/build"/*.idsig 2>/dev/null || true   # keep `ls build` to the two builds
printf '#!/bin/sh\nexec python3 "%s/shotfleet.py" "$@"\n' "$REPO" > "$S/bin/shotfleet"; chmod +x "$S/bin/shotfleet"
cat > "$S/rc" <<EOF
export PATH="$S/bin:\$PATH" BASH_SILENCE_DEPRECATION_WARNING=1
PS1='\[\e[1;33m\]\$\[\e[0m\] '
cd "$S/myapp"
EOF
cat > "$S/edits/shotfleet.toml" <<'EOF'
[ios]
app = "build/FleetFixture.app"
device_types = ["iPhone 17 Pro Max"]
runtime = "com.apple.CoreSimulator.SimRuntime.iOS-26-4"

[android]
apk = "build/FleetFixture.apk"
devices = ["phone"]
parallel = 2
EOF
cat > "$S/edits/flow.yaml" <<'EOF'
- launchApp
- waitForAnimationToEnd:
    timeout: 5000
- takeScreenshot: 01_welcome
- tapOn: "Next"
- waitForAnimationToEnd:
    timeout: 5000
- takeScreenshot: 02_settings
EOF
python3 - "$REPO/site/public/docs.html" "$S/myapp/.github/workflows/screenshots.yml" <<'EOF'
import html, re, sys
src = open(sys.argv[1], encoding="utf-8").read()
block = next(b for b in re.findall(r"<pre><code>(.*?)</code></pre>", src, re.S) if "screenshots.yml" in b)
open(sys.argv[2], "w").write(html.unescape(re.sub(r"<[^>]+>", "", block)).rstrip() + "\n")
EOF
ls "$S/myapp/build"
echo "session ready: $S"
