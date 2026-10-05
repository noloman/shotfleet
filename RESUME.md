# RESUME (agent on branch claude/workarounds-maestro-resources)

Goal: (A) pure capacity planner in shotfleet.py + tests/test_capacity_planner.py (not wired into run); (B) Maestro dependency risk summary from web;
(C) measurement plan. Deliverable: research/workarounds-maestro-resources-2026-10-05.md (< ~300 lines). No devices, no full test suites, no builds.
Allowed tests: `python3 -m unittest tests.test_capacity_planner tests.test_docs`. Use /usr/bin/git. Commit + push every <10 min, messages end `[skip ci]`.

Done: read the repo notes (existing fit_parallel/fit_emulators use memory_pressure level only; stall_s=900; MAESTRO_TESTED 2.0.10+2.11.0).
Left: planner + tests; web research (github.com/mobile-dev-inc/maestro releases); write the note; final reply (branch, commit, top 3, decisions).
Next step: see git log for the last commit.
