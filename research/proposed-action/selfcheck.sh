#!/bin/sh
# Offline check of the summary script and the YAML shape. Needs python3 (PyYAML optional). Run: sh research/proposed-action/selfcheck.sh
set -eu
cd "$(dirname "$0")"; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
echo '{"exit":1,"screenshots":["de/01.png","ja/01.png"],"problems":["ja/01.png: text looks like en, expected ja"],"notes":["x"]}' > "$T/j.json"
python3 summarize.py 1 "$T/j.json" /dev/null | grep -q "1 problem line" || { echo "FAIL summary"; exit 1; }
[ "$(python3 summarize.py --count "$T/j.json")" = 1 ] || { echo "FAIL count"; exit 1; }
printf 'line1\nsetup error: nope\n' > "$T/e.log"
python3 summarize.py 2 "$T/none.json" "$T/e.log" | grep -q "setup error: nope" || { echo "FAIL tail"; exit 1; }
python3 - <<'PY'
import sys
try: import yaml
except ImportError: print("PyYAML missing: YAML shape not parsed"); sys.exit(0)
a = yaml.safe_load(open("action.yml")); yaml.safe_load(open("example-workflow.yml"))
assert a["runs"]["using"] == "composite" and len(a["runs"]["steps"]) >= 4
print("yaml ok")
PY
echo "selfcheck ok"
