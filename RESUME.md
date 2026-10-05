# RESUME: branch claude/site-demo-evidence

Task: "See it work" page at /demo (site/public/demo.html) with demo clips and a dated EVIDENCE section, every sentence a claims row.
Device-free, light on CPU, no build, no deploy (the coordinator deploys through the release pipeline).

Done:
- site/public/demo.html: clips c1-doctor and c2-init live (files in site/public/media/demo/, copied from branch claude/demo-video,
  marketing/demo-video/web/); c3 to c9 wait in `<!-- CLIP <slug> ... CLIP -->` comments; evidence list; TODO comment for the Maestro measurement.
- Claims rows C140 to C153 (C132 is taken by PR #44's branch); demo.html added to C131's where list.
- Nav link "See it work" on index.html and docs.html; sitemap, llms.txt; _headers cache rule for /media/* (CSP unchanged:
  default-src 'self' already covers media and tracks); .clip styles in site.css; test_site.py checks posters and the video attributes.

Also done: CHANGELOG Unreleased line, docs/handoff.md section 15 line, tools/build-guides.py nav (the guides share the docs nav; site/draft/guides/*.html regenerate on the next build). Targeted tests green (226, 19 skipped).
Left for the coordinator: deploy through the release pipeline; add clips c3 to c9 as the page comment says.
Tests: python3 -m unittest tests.test_site tests.test_site_audit tests.test_claims tests.test_claims_unit tests.test_claims_site tests.test_docs tests.test_handoff_docs tests.test_golive
