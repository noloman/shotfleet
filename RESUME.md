# RESUME: GA4 investigation (2026-10-05)
Goal: why GA4 (G-6NY43DB3F4, property 557101981) shows no data for shotfleet.com. Deliverable research/ga4-investigation-2026-10-05.md (+ optional patch in research/proposed-ga4-fix/). Read-only: no site/GA changes.
Done: branch created; static read of ga.js/_headers/pages; live ga.js, analytics.js and / are byte-identical to repo; live CSP = repo CSP.
Left: browser test (?ga-test=), GA4 admin/realtime read-only, first-party counter numbers, Google docs check, write report, run python3 -m unittest tests.test_docs, push.
Next: Chrome test visit. Note: use /usr/bin/git (plain git is rewritten to rtk and refused in this worktree).
