# Resume: limits-catalan-check

Goal: write research/limits-catalan-check-macos-2026-10-05.md (4 questions: is the wger Catalan screen truly English; which languages Vision reads on macOS 14 vs 15+; what `check` should do on unreadable vs misjudged script; does README/site need a caveat). Research only, no code changes.

Branch: claude/limits-catalan-check (cut from origin/main). Worktree: /Users/manu/Developer/shotfleet/.claude/worktrees/agent-ae0aae5ba7805b570

Done so far:
- Branch created. Viewed research/real-apps-2026-10-04/wger-android-19-languages/ca-02_advanced.png: it shows English UI strings (Advanced, Server and authentication options, Self-hosted, Username and password, Refresh token, Ok).
- Original run (check.json, run.log) already flagged ca/02_advanced as 'shows en strings (13 lines) more than ca (0)', plus it, nl, pl, pt, pt-PT, ro, zh-Hant, ja on the same Advanced sheet: the app's Advanced sheet is untranslated in many locales. Full-size original PNG is not in the folder (only 3 downscaled PNGs, run.json, check.json, run.log).

Update: the note research/limits-catalan-check-macos-2026-10-05.md is written and the docs tests pass. Only the draft PR is left (see PR link below).

Original left list (all done except PR):
- Find wger app Catalan strings (not in repo; search was slow, do not run find on /).
- `.build/ocr` language list on this Mac (macOS 27), Apple docs URL for recognition languages.
- Read shotfleet.py: language detection, read_nothing, Tesseract fallback, 'treat a language problem as a hint'.
- grep README.md, site/public/*.html, tests/claims.json for language-check claims.
- Write the note, commit, run docs tests, push, open draft PR.

Docs tests: python3 -m unittest tests.test_docs tests.test_handoff_docs
PR command: gh pr create --draft --base main --head claude/limits-catalan-check
PR link: (none yet)

Next step: open the draft PR (gh pr create --draft --base main --head claude/limits-catalan-check), then put its link here.
