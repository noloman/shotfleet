#!/bin/sh
# Runs the "Run shotfleet" step of action.yml with a FAKE shotfleet on the PATH and the runner's output files faked.
# Checks: exit-code handling, the free-tier guard, the summary. Needs /usr/bin/ruby (to read the YAML) and bash. Not a GitHub run.
set -u
HERE=$(cd "$(dirname "$0")" && pwd); T=$(mktemp -d); trap 'rm -rf "$T"' EXIT; mkdir "$T/bin"
/usr/bin/ruby -ryaml -e 'a = YAML.load_file(ARGV[0]); File.write(ARGV[1], a["runs"]["steps"].last["run"])' "$HERE/action.yml" "$T/step.sh" 2>/dev/null
cat > "$T/bin/shotfleet" <<'EOF'
#!/bin/sh
[ "${FAKE_FREE:-0}" = 1 ] && echo "free tier: capturing 2 of 18 languages (ar, bg)." >&2
echo '{"exit":1,"screenshots":["a"],"problems":["x: bad"],"notes":[]}'
exit "${FAKE_EXIT:-1}"
EOF
chmod +x "$T/bin/shotfleet"
step() { # command fail-on-problems require-licence -> prints exit code of the step
  : > "$T/out"; : > "$T/sum"
  ( cd "$T" && PATH="$T/bin:$PATH" GITHUB_OUTPUT="$T/out" GITHUB_STEP_SUMMARY="$T/sum" SF_COMMAND="$1" SF_ARGS="shots/" \
    SF_FAIL_ON_PROBLEMS="$2" SF_REQUIRE_LICENCE="$3" SF_ACTION="$HERE" /bin/bash "$T/step.sh" >/dev/null 2>&1 ); echo $?
}
fail() { echo "FAIL: $1"; exit 1; }
[ "$(step check true true)" = 1 ] || fail "problems should fail the step"
grep -q "problems=1" "$T/out" && grep -q "x: bad" "$T/sum" || fail "outputs or summary"
[ "$(step check false true)" = 0 ] || fail "fail-on-problems false should pass"
FAKE_EXIT=0; export FAKE_EXIT
[ "$(step check true true)" = 0 ] || fail "exit 0 should pass"
FAKE_FREE=1; export FAKE_FREE
[ "$(step run true true)" = 2 ] || fail "free tier with require-licence should fail with 2"
[ "$(step run true false)" = 0 ] || fail "free tier allowed should pass"
[ "$(step bogus true true)" = 2 ] || fail "unknown command should be refused"
echo "steptest ok"
