#!/bin/sh
# Copy skill/* into a checkout of the public repo noloman/shotfleet-skills, set its plugin version to
# shotfleet's VERSION, and print the diff. It never commits or pushes: read the diff, then commit and push yourself.
#   sh tools/sync-public-skills.sh <path to a shotfleet-skills checkout>
set -eu
[ $# -eq 1 ] || { echo "usage: sh tools/sync-public-skills.sh <shotfleet-skills checkout>" >&2; exit 2; }
ROOT=$(cd "$(dirname "$0")/.." && pwd)
DEST=$1
[ -f "$DEST/.claude-plugin/plugin.json" ] && [ -d "$DEST/.git" ] \
  || { echo "sync-public-skills: $DEST is not a shotfleet-skills checkout" >&2; exit 2; }
VERSION=$(sed -n 's/^VERSION = "\(.*\)"$/\1/p' "$ROOT/shotfleet.py")
[ -n "$VERSION" ] || { echo "sync-public-skills: no VERSION in shotfleet.py" >&2; exit 2; }

mkdir -p "$DEST/skills"
for d in "$ROOT"/skill/*/; do
  name=$(basename "$d")
  [ -f "$d/SKILL.md" ] || continue
  rm -rf "${DEST:?}/skills/$name"
  cp -R "$d" "$DEST/skills/$name"
done
# A skill removed here is removed there too.
for d in "$DEST"/skills/*/; do
  [ -d "$d" ] && [ ! -d "$ROOT/skill/$(basename "$d")" ] && rm -rf "$d"
done

python3 - "$DEST/.claude-plugin/plugin.json" "$VERSION" <<'EOF'
import json, sys
path, version = sys.argv[1], sys.argv[2]
data = json.load(open(path))
data["version"] = version
open(path, "w").write(json.dumps(data, indent=2) + "\n")
EOF

git -C "$DEST" add -A
git -C "$DEST" --no-pager diff --cached --stat
git -C "$DEST" --no-pager diff --cached
echo "sync-public-skills: staged in $DEST for shotfleet $VERSION; nothing committed or pushed." >&2
