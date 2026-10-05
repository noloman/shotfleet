# RESUME (delete before merging)

Goal: make the free-tier cap message in `shotfleet.py` say (a) the run is limited to 2 languages because there is no valid licence, plus why a SHOTFLEET_KEY was refused, (b) which 2 were captured and that `--locales a,b` picks others. Wording only; exit codes and licence logic unchanged.

Done:
- shotfleet.py: LOCALE_CAP_WHY, cap_locales message, apply_free_tier sets the reason when SHOTFLEET_KEY is set.
- tests/test_free_tier_message.py (6 tests: no key, refused key, not-a-key, unreachable server = no cap, --locales, licensed).
- CHANGELOG.md Unreleased line, skill/shotfleet/references/licence.md.
- Targeted tests pass (test_free_tier_message, test_claims_unit, test_agent_skills, test_docs, test_release_candidate, test_handoff_docs).

Left:
- run tests/test_shotfleet.py output check, targeted claims tests (tests/test_claims.py), site/README text check.
- ONE full `tools/check-claims.sh > <file> 2>&1` after `pgrep -f tools/check-claims.sh` shows no other run (poll 30 s). Record exit code and test count.
- Draft PR: `gh pr create --draft --base main --head claude/fix-free-tier-message` (body: old/new message, tests, exit code, 'Merge with [skip ci]', RESUME.md must be deleted before merging).

Tests: `cd tests && python3 -m unittest test_free_tier_message test_claims_unit test_agent_skills test_docs test_release_candidate`

PR: not opened yet.
Next step: run test_shotfleet and test_claims, then the single full check.
