# RESUME (release-pipeline, shotfleet 0.1.2 group A; coordinator deletes this before merge)

Goal: A1 packaging/publish.sh, A2 packaging/preflight.sh, A3 tools/verify-release.sh, A4 tests/test_release_consistency.py + shell tests, A6 stale files, plus packaging/README.md and a CHANGELOG line. Device-free. No real deploy, no Cloudflare writes. A5 is not mine.
Branch claude/release-pipeline (from origin/main). Use /usr/bin/git. Push with: /usr/bin/git push -u origin claude/release-pipeline. Commit messages end in [skip ci].
Verify with targeted tests only: python3 -m unittest tests.test_release_consistency tests.test_release_candidate tests.test_docs tests.test_handoff_docs tests.test_claims; sh -n on new scripts.

Done: A6 (shotfleet.spec, packaging/shotfleet.rb deleted; DISTRIBUTION.md line fixed).
Left: A1, A2, A3, A4, README, CHANGELOG.
