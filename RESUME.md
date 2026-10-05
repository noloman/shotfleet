# RESUME (delete before merging)

Goal: `--json` on a check/run over several reports prints ONE document covering all of them (single report unchanged).
Branch: claude/fix-json-multi-report (from origin/main). PR: not opened yet.

Done: shotfleet.py (REPORTS list + reports_json(), used by main --json and mcp_call), tests/test_json_multi_report.py
(fails on old main, passes now), docs (README line 92, skill/shotfleet/SKILL.md, skill/shotfleet/references/ci.md).
Left: ONE full `tools/check-claims.sh` (wait while `pgrep -f tools/check-claims.sh` shows another run; output to a file, record exit code),
commit, push, open DRAFT PR (body: change, test, full-check exit code and test count, 'Merge with [skip ci]', RESUME.md must be deleted before merging, last line the Generated-with-Claude-Code line).

Tests: python3 -m unittest tests.test_json_multi_report tests.test_agent_skills tests.test_cli_claims tests.test_docs
Next step: run the full check once (no other run active).
