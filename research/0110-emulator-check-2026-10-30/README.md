# 0.1.10 emulator check of the new features, 2026-10-30

The signed 0.1.10 build (Maestro 2.0.10, Google APIs emulator image) ran shotfleet.toml and flow.yaml here on the Android fixture app, de and en, devices phone and a custom 1920x1080 landscape phone.

Worked: `clock` and `root` (status bar shows 10:00 in the landscape picture), the custom size and landscape (1920x1080 PNG, emulator booted wider than tall), `waitForExpected` (the flow ran, no warning), `runFlow` with `when: { defined: phrase }` (de took 3 screenshots, en 2, run.json lists `skipped_screenshots: ["01b_phrase"]` for en).

Found: `check` reports "en: missing 01b_phrase.png" as a problem and exits 1, though en skipped it on purpose. docs/screenshot-mode.md already said what check makes of the gap was not tested. To fix in the next release.

Not run: foldables, the Compose hint, the notification recipes, `[inputs]` typing (needs Maestro 2.11.0).
