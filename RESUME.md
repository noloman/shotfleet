# RESUME: claude/013-versioned-urls

Task: versioned permanent URLs /download/<version>/<file> on shotfleet.com (publish.sh re-stages every archived version each deploy).

Done:
- [x] publish.sh: check_archive (SHA256SUMS + kept manifest), PLAN of versioned files, dry-run plan, staging after the archive step, post-deploy verification of every versioned file, Cache-Control immutable warning
- [x] site/public/_headers: /download/:file no-cache, /download/:version/* immutable (no /download/* any more: rules would join values)
- [x] tests/test_release_scripts.py class Versioned (6 tests), 32/32 green
Next:
- [x] docs: packaging/README.md, CHANGELOG Unreleased, docs/handoff.md note
- [ ] staging rehearsal (staging only), in a clean export tree (publish.sh refuses a tree with RESUME.md)
- [x] targeted tests (85 ran, 6 skipped): test_release_scripts test_release_consistency test_docs test_handoff_docs test_golive
