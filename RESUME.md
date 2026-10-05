# RESUME: A5 pinned build inputs (branch claude/pinned-build-inputs)
Goal: packaging/build.sh installs exact hashed inputs (packaging/requirements-build.txt) with the recorded uv Python 3.14.2; no wrapper.
Done: requirements-build.txt (7 wheels, hashes from one PyPI download 2026-10-05), build.sh (Python version + minos check, fresh venv, --require-hashes), build-linux.sh (exact versions, no hashes), preflight.sh looks for 3.14.2, tools/release-candidate.sh copies tools/ (build.sh runs macho-minos), tests/test_pinned_build_inputs.py, README + CHANGELOG. Scratch-venv install with --no-index --find-links passed; hash mismatch rejected; PyInstaller --version = 6.22.3.
Left: targeted tests green, push. Nothing else.
Next: coordinator merges; DELETE RESUME.md before merging. A full signed build with the pins is not run.
