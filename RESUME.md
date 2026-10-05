# RESUME: publish.sh staging rehearsal (branch claude/publish-staging-rehearsal)

Delete this file before merge (publish.sh refuses a tree containing it).

ALL STEPS DONE 2026-10-05 ~15:00. Only the final report to the coordinator remains (branch, commit, results below).
- shotfleet-staging did not exist; created as a plain worker (no routes, no bindings) via site/wrangler.staging.toml; URL https://shotfleet-staging.manulorenzop.workers.dev
- publish.sh --staging + guards, tests (26 green), smoke.sh SMOKE_SKIP_REDIRECT, README section.
- Rehearsal: bootstrap 0.1.0 d6be78d2; publish 0.1.1 b7662280 (smoke 35/0, install ok); manual rollback to d6be78d2 ok (~7 s); auto-rollback via forced smoke failure (1c558343 -> d6be78d2) ok; deploy without download/ (8db83083) => /download/* 404, deletion theory confirmed; staging restored to d6be78d2 (0.1.0).
- A PRODUCTION deploy b64119e0 at 12:55:12Z is NOT mine (all my writes used --name shotfleet-staging).
- Logs: /Users/manu/Developer/shotfleet-rc-build/staging-rehearsal/{real-run.log,auto-rollback-run.log}; scratch tree staging-rehearsal-tree (git worktree, remove when done).
