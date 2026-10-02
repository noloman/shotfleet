#!/bin/sh
# Every promise on the site and in the docs is tested: the unit tests (program, site, claims register) and the site worker's tests.
# One line at the end; full output only when something fails. Used by .githooks/pre-commit, CI and packaging/release.sh.
cd "$(dirname "$0")/.." || exit 1
out=$(mktemp); trap 'rm -f "$out"' EXIT
python3 -m unittest discover -s tests >"$out" 2>&1; py=$?
py_line=$(grep -E '^(Ran |OK|FAILED)' "$out" | tr '\n' ' ')
node site/worker.test.mjs >>"$out" 2>&1; js=$?
js_ok=$(grep -c '^ok' "$out"); js_bad=$(grep -c '^FAIL' "$out")
if [ $py -ne 0 ] || [ $js -ne 0 ]; then cat "$out"; echo "check-claims: FAILED (python: ${py_line:-no result}; worker: $js_ok ok, $js_bad failed)"; exit 1; fi
echo "check-claims: ok (python: $py_line; worker: $js_ok checks ok)"
