# RESUME (release-pipeline, shotfleet 0.1.2 group A; coordinator deletes this before merge)

Goal: A1 packaging/publish.sh, A2 packaging/preflight.sh, A3 tools/verify-release.sh, A4 tests/test_release_consistency.py + shell tests, A6 stale files, plus packaging/README.md and a CHANGELOG line. Device-free. No real deploy, no Cloudflare writes. A5 is not mine.
Branch claude/release-pipeline (from origin/main). Use /usr/bin/git. Push with: /usr/bin/git push -u origin claude/release-pipeline. Commit messages end in [skip ci].
Verify with targeted tests only: python3 -m unittest tests.test_release_consistency tests.test_release_candidate tests.test_docs tests.test_handoff_docs tests.test_claims; sh -n on new scripts.

Done: A6 (shotfleet.spec, packaging/shotfleet.rb deleted; DISTRIBUTION.md line fixed).
Left: A2, A4 (tests for A1+A3 too), README, CHANGELOG. A1 publish.sh and A3 verify-release.sh written (A3 run read-only on the real 0.1.1 files: PASS 12 checks); A1 only syntax-checked so far.
