# RESUME (docs refresh, delete before merge)

Goal: apply research/docs-audit-2026-10-05.md (on origin/claude/docs-audit) section (e) order. Branch claude/docs-refresh, cut from origin/main 44cd5f2. Device-free, targeted tests only, commits end with [skip ci].
Git note: the rtk hook blocks plain `git`; use `/usr/bin/git`.

Coordinator follow-up (Manu approved, apply AFTER the first pass, push after each):
 (1) D1 privacy.html waitlist text to past tense (rows C078, C086, tests/test_claims_site.py; do not claim the list was deleted unless repo/STATUS says so)
 (2) D3 exact sentence 'Built for macOS 13 or later on Apple silicon; tested on macOS 27.' on index.html (price lede + Not for you if), alternatives.html:89, llms.txt, JSON-LD softwareRequirements (prefix 'macOS 13 or later on an Apple silicon Mac, '), SKILL.md, AGENTS-snippet; C131 where list
 (3) D7/B9 README quickstart reorder (install, doctor --fix, init, run, then activate), xcode-select -p, first doctor note, per research/limits-first-run-2026-10-05.md; mirror docs.html + skill; fix quoting tests/claims
 (4) D5 'measured on Maestro 2.0.10' next to 9 min iOS / 15 Android on index.html and alternatives.html; C007, C105
 Still NOT approved: terms.html, licence design, D8 founder price, marketing/**, site/draft/**.
 Also second llms.txt bullet of A8 ("when you buy or write to me") depends on D1: do it with item (1).

Done: A1-A9, B1-B8, B10, C1-C17 (research/README.md written; update its first-run line after follow-up 3), C16 proofs. First pass COMPLETE.
Left: follow-up (1)-(4)
Skipped on purpose: section (d) items not approved
Next step: follow-up (4) D5 first (smallest), then (2) D3, (3) D7/B9, (1) D1
