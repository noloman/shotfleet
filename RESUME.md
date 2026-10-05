# RESUME (branch claude/fix-device-type-fallback)
Goal: default iPhone type falls back to newest iPhone N Pro Max when Xcode lacks the 17; explicit device_type untouched.
Done: default_device_type in shotfleet.py (from research/proposed-platform-reach patch, shotfleet.py hunks only; packaging hunk already on main), tests/test_device_type_fallback.py, config.md, CHANGELOG. README line 314 left alone (site/docs.html mirrors it).
Left: nothing. Next: coordinator review. RESUME.md deleted before merge.
