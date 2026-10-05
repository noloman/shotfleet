# RESUME: publish.sh staging rehearsal (branch claude/publish-staging-rehearsal)

Delete this file before merge (publish.sh refuses a tree containing it).

Findings (2026-10-05 ~14:45): worker `shotfleet-staging` did NOT exist on the account (wrangler deployments list: code 10007). Production `shotfleet` exists, workers.dev subdomain `manulorenzop`, routes shotfleet.com + www as custom domains, KV WAITLIST, ratelimit, send_email. Staging config added: site/wrangler.staging.toml (no routes, no bindings, only [assets]); URL https://shotfleet-staging.manulorenzop.workers.dev (created as a plain new worker, no production data; G9 used the same name before).

Done: step 1 publish.sh --staging + guards + tests (26 green), smoke.sh SMOKE_SKIP_REDIRECT.
Todo: step 2 bootstrap staging with 0.1.0 bytes (previous version), step 3 manifest+dry-run+real 0.1.1 deploy to staging, step 4 rollback test, step 5 README + final report.
Rehearsal tree: scratch worktree of this branch with RESUME.md removed locally (PUBLISH_ALLOW_BRANCH=1). Release dir: /Users/manu/Developer/shotfleet-rc-build/staging-rehearsal (state under staging/).
