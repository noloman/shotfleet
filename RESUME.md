# RESUME (delete before merging)

Goal: `--json` on a check/run over several reports prints ONE document covering all of them (single report unchanged).
Branch: claude/fix-json-multi-report (from origin/main). PR: draft, see `gh pr view --head claude/fix-json-multi-report`.

Done: shotfleet.py (REPORTS list + reports_json(), used by main --json and mcp_call), tests/test_json_multi_report.py
(fails on old main, passes now), docs (README line 92, skill/shotfleet/SKILL.md, skill/shotfleet/references/ci.md).
Full `tools/check-claims.sh` ran once: exit 0, 856 tests (21 skipped), worker 59 checks ok. Do not run it again.

Tests: python3 -m unittest tests.test_json_multi_report tests.test_agent_skills tests.test_cli_claims tests.test_docs
Next step: nothing; the owner reviews, RESUME.md is deleted before merge.
