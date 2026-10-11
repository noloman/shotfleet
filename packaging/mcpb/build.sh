#!/bin/sh
# Builds shotfleet.mcpb from manifest.json and server/ next to this script. Local only: it publishes nothing.
#   sh build.sh [output.mcpb]      MCPB="node /path/to/mcpb.js" to use an installed copy instead of npx
# The version in manifest.json must match shotfleet.py when this folder sits inside the shotfleet repo.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=${1:-$here/shotfleet.mcpb}
mcpb=${MCPB:-npx -y @anthropic-ai/mcpb@2.1.2}   # the official package, pinned
mv=$(sed -n 's/^  "version": "\(.*\)",/\1/p' "$here/manifest.json")
if [ -f "$here/../../shotfleet.py" ]; then
  pv=$(sed -n 's/^VERSION = "\(.*\)"/\1/p' "$here/../../shotfleet.py")
  [ "$mv" = "$pv" ] || { echo "manifest.json says $mv but shotfleet.py says $pv" >&2; exit 1; }
fi
[ -x "$here/server/shotfleet-mcp" ] || { echo "server/shotfleet-mcp is missing or not executable" >&2; exit 1; }
stage=$(mktemp -d); trap 'rm -rf "$stage"' EXIT
cp "$here/manifest.json" "$stage/"; mkdir "$stage/server"; cp -p "$here/server/shotfleet-mcp" "$stage/server/"
$mcpb validate "$stage/manifest.json"
$mcpb pack "$stage" "$out"
echo "built $out (shotfleet $mv)"
