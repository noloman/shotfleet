# RESUME (delete before merging)

Goal: make the free-tier cap message in `shotfleet.py` say (a) the run is limited to 2 languages because there is no valid licence, plus why a SHOTFLEET_KEY was refused, (b) which 2 were captured and that `--locales a,b` picks others. Wording only; exit codes and licence logic unchanged.

Done:
- shotfleet.py: LOCALE_CAP_WHY, cap_locales message, apply_free_tier sets the reason when SHOTFLEET_KEY is set.
- tests/test_free_tier_message.py (6 tests: no key, refused key, not-a-key, unreachable server = no cap, --locales, licensed).
- CHANGELOG.md Unreleased line, skill/shotfleet/references/licence.md.
- Targeted tests pass (test_free_tier_message, test_claims_unit, test_agent_skills, test_docs, test_release_candidate, test_handoff_docs).

Left:
- Nothing in code. Full tools/check-claims.sh ran once: exit 0, 860 tests OK (skipped=21), worker 59 checks ok.
- Delete this file before merging. Do not merge (draft PR).

Tests: `cd tests && python3 -m unittest test_free_tier_message test_claims_unit test_agent_skills test_docs test_release_candidate`

PR: see `gh pr view --head claude/fix-free-tier-message`
Next step: wait for the coordinator to review the draft PR.
