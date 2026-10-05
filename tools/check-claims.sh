#!/bin/sh
# Every promise on the site and in the docs is tested: the unit tests (program, site, claims register) and the site worker's tests.
# One line at the end; full output only when something fails. Used by .githooks/pre-commit, CI and packaging/release.sh.
# The test modules run at once, one process each (half the cores; CHECK_JOBS=n to choose): most of their time is waiting on
# subprocesses, not CPU. Each is discovered on its own like `python3 -m unittest discover -s tests`, so test names stay the same.
cd "$(dirname "$0")/.." || exit 1
d=$(mktemp -d); trap 'rm -rf "$d"' EXIT
jobs=${CHECK_JOBS:-$(( $(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 2) / 2 ))}; [ "$jobs" -ge 1 ] 2>/dev/null || jobs=1
t0=$(date +%s)
# biggest files first: roughly the slowest modules first, so none starts last
ls -S tests/test_*.py | xargs -P "$jobs" -I {} sh -c 'm=$(basename "$1" .py)
  python3 -m unittest discover -s tests -p "$m.py" >"$2/$m.out" 2>&1 || echo "$m" >>"$2/failed"' _ {} "$d"
secs=$(( $(date +%s) - t0 ))
py_line=$(awk -v secs="$secs" -v failed="$(cat "$d/failed" 2>/dev/null | tr '\n' ' ')" '
  /^Ran [0-9]+ tests? in / { ran[FILENAME] = $2 }  # the last summary of each module counts, not a test that prints one
  /^(OK|FAILED)( \(.*\))?$/ { last[FILENAME] = $0 }
  END {
    for (f in ran) total += ran[f]
    for (f in last) { s = last[f]; while (match(s, /[a-z ]+=[0-9]+/)) { split(substr(s, RSTART, RLENGTH), kv, "="); sub(/^ +/, "", kv[1]); n[kv[1]] += kv[2]; s = substr(s, RSTART + RLENGTH) } }
    split("failures|errors|skipped|expected failures|unexpected successes", order, "|")
    for (i = 1; i <= 5; i++) if (n[order[i]]) parts = parts (parts ? ", " : "") order[i] "=" n[order[i]]
    bad = n["failures"] + n["errors"] + n["unexpected successes"] > 0 || failed != ""
    status = (bad ? "FAILED" : "OK") (parts ? " (" parts ")" : "") (failed != "" && !(n["failures"] + n["errors"]) ? " (exit status != 0: " failed ")" : "")
    printf "Ran %d tests in %ds %s ", total, secs, status }' "$d"/*.out)
[ -s "$d/failed" ] && py=1 || py=0
node site/worker.test.mjs >"$d/worker" 2>&1; js=$?
js_ok=$(grep -c '^ok ' "$d/worker"); js_bad=$(grep -c '^FAIL ' "$d/worker")
if [ $py -ne 0 ] || [ $js -ne 0 ]; then cat "$d"/*.out "$d/worker"; echo "check-claims: FAILED (python: ${py_line:-no result}; worker: $js_ok ok, $js_bad failed)"; exit 1; fi
echo "check-claims: ok (python: $py_line; worker: $js_ok checks ok)"
