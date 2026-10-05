# RESUME (branch claude/fix-relative-app-path)
Goal: init writes the app path relative when inside the project; run/check resolve relative to the config folder; absolute still works; note when outside.
Finding: relative-inside-project ALREADY worked on main (config_path); added the one-line note for outside builds, normpath in load_config path(), tests/test_relative_app_path.py, README/config.md/CHANGELOG.
Left: nothing. Next: coordinator review. RESUME.md deleted before merge.
