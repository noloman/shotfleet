#!/bin/sh
# Run the two upstream watchers on this machine (about once a month, and before a release): the newest stable Maestro against what shotfleet relies on, and
# Apple's screenshot specification page against shotfleet's size table. No GitHub Actions needed. Exit 0 only if both pass; 1 means something to update
# (read the lines above it); 2 means a watcher could not read its source (offline, or the page changed shape).
cd "$(dirname "$0")/.." || exit 2
status=0
echo "== newest Maestro release (tools/latest-maestro.py; downloads about 315 MB)"
python3 tools/latest-maestro.py || status=$?
echo
echo "== Apple screenshot sizes (tools/apple-specs-watch.py)"
python3 tools/apple-specs-watch.py || { s=$?; [ "$status" -lt "$s" ] && status=$s; }
echo
[ "$status" -eq 0 ] && echo "watch-upstream: both ok" || echo "watch-upstream: exit $status (see above)"
exit "$status"
