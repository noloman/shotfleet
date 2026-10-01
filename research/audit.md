# shotfleet audit (shotfleet.py, 1002 lines, README.md)

Method: full read of shotfleet.py and README.md, plus throwaway scripts (scratchpad `audit/t1.py`, `t2.py`, `t3.py`) calling pure functions with fixtures. No simulator, emulator, Maestro or `run` was started. CONFIRMED = reproduced; TRACED = from code only.
Line numbers refer to the current shotfleet.py.

## Ranked findings

### 1. [HIGH, CONFIRMED] export wipes an existing listing and ignores run failures (data loss, bad shots exported)
shotfleet.py:919-951 (deletion at 947; `bad` built at 923-926).
- Defect A: `export` decides what is "bad" only from check.json problems, and `check` only knows locales that have at least one PNG. A locale whose capture produced 0 screenshots has no label in `find_screenshots`, so it is never flagged "missing". Export then deletes every `*.png` in the existing fastlane folder (line 947) and copies nothing.
- Defect B: run.json's per-locale `ok:false` is never consulted. If every locale stops at the same step, all sets are equally short, "missing" is never raised, and the partial sets are exported with exit 0. README says failed languages are skipped.
- Defect C: line 947 deletes ALL `*.png` in `screenshots/<locale>/`. fastlane deliver keeps every device size (iPad, 6.5") in that one folder, so the user's other-device screenshots are destroyed.
- Repro (t2.py F5): out/raw/de empty, raw/fr has 1 png, run.json ok:false for both, check.json problems=[]. fastlane/screenshots/de-DE has old_iphone.png and iPad_13.png. Result: "exported 2 listings", rc 0, de-DE now empty (both files gone), fr-FR/01.png written.
- Fix: in export, skip any locale where run.json says `ok` is false or the raw dir has no PNGs (`if not pngs: continue`) before touching dst. Delete only files that this export replaces by name (or only names matching raw/lp), not all `*.png`. Return non-zero if check.json is missing.

### 2. [HIGH, CONFIRMED] Script shortcut in judge_screen lets wrong-language screenshots pass
shotfleet.py:712-714.
- Defect: when fewer than 2 lines match any strings table (the normal case for screens full of dynamic content), any 3 characters in the expected language's Unicode block count as proof. Cyrillic is shared by ru and uk, Han by zh-Hans, zh-Hant and ja kanji, Arabic by ar, fa and ur.
- Repro (t1.py F4): `judge_screen("uk", <Russian screen>, tables)` returns `('uk', None)`. A Japanese kanji screen in the `zh-Hans` folder passes. A Traditional Chinese screen in the `zh-Hans` folder passes. The README advertises catching a wrong-language folder, and this lets ru into uk, and zh-Hant into zh-Hans, through whenever string matching is thin.
- Fix: use the script test only as a negative filter (no script chars means fail). For shared-script pairs (ru/uk/bg/sr, zh Hans/Hant/ja, ar/fa/ur), also require `ocr["lang"]`/`langs` to agree, or use a distinguishing char set (ukrainian `іїєґ`, kana for ja).

### 3. [HIGH, CONFIRMED] Uncaught exceptions give a traceback and exit 1 (which README defines as "problems found")
main_cmd catches only Fail and RuntimeError (shotfleet.py:994). Confirmed paths:
- `localize_flow` raises ValueError (shotfleet.py:289, 296) for a flow without a literal `\n---\n` (CRLF files, `--- ` with trailing space), and for `- launchApp:` with options. The `launchApp` case is the very limitation README documents; it should be a clean message. Repro t1 F2. On Android the same ValueError (line 566) is raised in `round_` after the emulators are booted.
- `junit_results` (396): `xml.etree.ElementTree.ParseError` when Maestro was killed mid-write, e.g. right after the timeout kill in `run_guarded`. Repro t2 F9. This crashes before results/run.json are written.
- `shipped_locales` KeyError (below, #5), TOML `parallel = "4"` TypeError (439), `subprocess.TimeoutExpired` from `Emu.adb`/`booted` (516-522) and from `p.wait(120)` (552), FileNotFoundError when `adb`, `xcrun` or the emulator binary is missing (`run` never checks them).
- Fix: catch `(Fail, RuntimeError, ValueError, ParseError, subprocess.TimeoutExpired, OSError, KeyError)` in `main_cmd`, print one line, return 2. Turn the `launchApp` ValueError into a Fail naming the flow line.

### 4. [HIGH, TRACED] Emulator and simulator leaks
- android_pool first boot (550-552): the writable first-boot emulator on port 5700 is a Popen that is never added to `pool`. If `wait_booted` raises (600 s) or `p.wait(timeout=120)` raises TimeoutExpired (the `reboot -p` failed), the `finally` in android_run (659-660) only kills `pool`, so that emulator runs forever. Fix: add the emulator to `pool` (or `try/finally: e.adb("emu","kill")`).
- SIGTERM (CI cancel, `timeout`, kill) is not handled; only KeyboardInterrupt is. Python dies without running `finally`, leaving up to 4 emulators and Maestro/driver processes. Fix: `signal.signal(SIGTERM, lambda *_: sys.exit(143))` so the `finally` runs.
- iOS (make_pool 311-330, cmd_run): simulators are booted and never shut down on success, failure or Ctrl-C, and the status-bar override persists. The Ctrl-C message "may still be running" is also wrong for Android, where `finally` does kill them. Fix: `simctl shutdown` of pool in a `finally` (or document and print "N simulators left running").
- run_guarded (345-365): on KeyboardInterrupt, `proc` (Maestro) is not killed; on timeout the maestro log is never written because `write_text` (464) is after the call that raised, so the one case that needs the log has none. Fix: wrap communicate in try/except BaseException to kill descendants, and write partial output in the TimeoutExpired handler (`e.output`).

### 5. [MEDIUM, CONFIRMED] shipped_locales drops partially translated languages and crashes without an `en` table
shotfleet.py:191-205.
- Defect A: the "own strings" set is defined as keys translated into fewer than 90% of the top count. With one extra language, own = the keys that are NOT translated. Repro (t1 F3): en has 100 keys, de translates 80: returns `['en']`, de is dropped. With de 100% and fr 80%: fr is dropped. Android `run` default locales silently omit these; `check --app` then reports "the app has no fr translation" for a real, mostly translated listing.
- Defect B: `strings[base]` with base hardcoded "en": an APK or .app whose base_locale is not en and that has no `en` table raises KeyError (check --app, init, android_run line 588 ignores `base_locale` config). Repro: `shipped_locales({"de":..., "fr":...})` raises KeyError 'en'.
- Fix: define own keys as those absent from the near-universal library set (count >= 0.9*top across >= 20 locales), else all keys; pass `base` everywhere (`cmd_check`, `cmd_init`, android_run).

### 6. [MEDIUM, CONFIRMED] Inline-map selectors are never translated or reported, and README's own tip uses one
shotfleet.py:228. `if raw.startswith(("{", "[", ...))` assumes a following-lines map, but `- tapOn: { text: "Accept", optional: true }` is complete on one line. Repro (t1 F1): it is left in English, not added to `untranslated_selectors`, no warning. README Tips shows exactly `- tapOn: { text: "Accept", optional: true }`, so in every non-English locale the dismissal silently no-ops and the flow stalls. Same for `{ text: ... }` in `assertVisible`.
- Fix: for `{...}` values, regex-replace `text:\s*("[^"]*"|'[^']*'|[^,}]+)` inside the braces using the same translation, or at least append the selector to `missing`.

### 7. [MEDIUM, CONFIRMED] iOS default locale list includes languages the app does not ship; init and check disagree
shotfleet.py:417 (`sorted(strings)`), 895.
- Defect: Android filters with `shipped_locales`; iOS uses every lproj that has any `.strings` table. Apps commonly localize only InfoPlist.strings (display name, permission texts) into 30 languages, and embedded frameworks ship their own lprojs. Repro (t2 F8): fr.lproj with only InfoPlist.strings gives `load_strings` = `['en','fr']`, so run boots a flow for fr that shows English. Then `cmd_check` (run passes the unfiltered `strings`) reports "shows en strings", wasting simulator time. `check --app` filters through `shipped_locales`, so the same app is judged differently. README: "every language your app ships".
- Fix: apply `shipped_locales(strings, base_locale)` in the iOS branch too (and in `cmd_run`'s check call).

### 8. [MEDIUM, CONFIRMED] check false positives: en-US/en-GB, es-ES/es-MX copies in no-`--app` mode
shotfleet.py:790-803 (`lp or label` when `tables` is empty).
- Defect: without `--app`, `lp` is None so each store folder is its own "language". Identical English screenshots in `en-US`, `en-GB`, `en-AU` (the common case) are reported "identical image in 2 languages". Repro (t2 F7): rc 1, one problem. The code comment on line 802 says same-language copies are fine, but that only holds with `--app`.
- Fix: group labels by `canon(label).split("-")[0]` as the language when `lp` is None.

### 9. [MEDIUM, CONFIRMED] find_screenshots picks one layout and ignores the rest; jpg files are invisible
shotfleet.py:726-736.
- Defect A: if a folder holds both iOS `screenshots/` and `metadata/android/...` (the usual fastlane/ root, and what the README shows for `check fastlane/`), only the first matching pattern is checked. Repro (t2 F6): returns only the Android labels, and iOS PNGs are never checked or reported; with `--app MyApp.app` the Android folders are checked against iOS strings.
- Defect B: only `*.png`; `.jpg/.jpeg` screenshots (both stores accept them) are skipped silently. A folder where some locales use jpg yields "missing" for them, or "no screenshots found" when all are jpg.
- Fix: choose the layout by the `--app` suffix (or process every layout found and label with platform); glob case-insensitively over png/jpg/jpeg.

### 10. [MEDIUM, TRACED] Reused simulators are not validated against device_type/runtime settings
shotfleet.py:313-319. `by_name[name]` is reused by name only. If the user changes `device_type` (iPhone 6.9" to iPad, or any other size) the old shotfleet-N simulators keep being used and screenshots come out at the wrong size, silently. Duplicate-named simulators also collide (last wins). Fix: compare `d["deviceTypeIdentifier"]` with device_type, and delete/recreate on mismatch (or include the type in the name).

### 11. [MEDIUM, TRACED] `run` can delete unrelated user folders under `out`
shotfleet.py:421, 592. `shutil.rmtree(out/"flows")`, `out/"debug"`, `out/"tmp"` and `out/junit*.xml` are removed unconditionally. With `out = "."` (plausible for a config sitting in a project that keeps Maestro flows in `flows/`), the project's flow folder is deleted. Fix: refuse (Fail) unless `out` is empty or contains run.json, or nest everything under `out/.shotfleet/`.

### 12. [LOW-MEDIUM, CONFIRMED] check silently weakens when run.json's app is gone
shotfleet.py:770-773. If `run["app"]` no longer exists (rebuilt DerivedData), `load_strings` returns `{}` (rglob of a missing dir), and `check` runs in detection-only mode with no warning (the "no --app given" notice is suppressed because run.json exists). Repro (t2 F11). Fix: Fail if the stored path is missing and `--app` was not given.

### 13. [LOW, CONFIRMED] `--json` prints `{"exit":1}` without problems when no screenshots are found
shotfleet.py:777-778 returns before `LAST_REPORT` is set, so main prints only `{"exit": 1}` (README promises `screenshots`/`problems`). TRACED (my t2 run reused one process and picked up a stale LAST_REPORT, so not a clean repro). Fix: write a minimal report with a problem string before returning.

### 14. [LOW, CONFIRMED] Misleading or sloppy input handling
- `--locales "de, ja"` leaves `" ja"` ("skip  ja: app has no  ja.lproj", shotfleet.py:987); an unknown locale is only a "skip" line while rc stays 0 when others succeed. Fix: strip, and Fail on unknown locales.
- redirect_screenshot (256): `- takeScreenshot: 01_home  # hero` becomes file `01_home  # hero.png` (t2 F10); exported to fastlane with that name and the `#` breaks gallery URLs (832, unencoded href). Also `{ path: x }` flow-map form is not redirected, so shots land in cwd and count 0. Fix: strip trailing ` #...`, `urllib.parse.quote` the gallery URL.
- Single-quoted YAML selectors with `''` (`'It''s'`) and values with embedded newlines are not matched or break the generated flow (230, 208).
- cmd_init writes `apk = "{app}"` into TOML unescaped (891, 896); a path with `"` or `\` produces invalid TOML. Use `json.dumps(str(app))`.
- android_flow (568): `re.match(r"\s*- launchApp", body.lstrip())` fails when the first body line is a comment, which is true for FLOW_TEMPLATE, so a second `- launchApp` is inserted (harmless but a double launch). On iOS the template also launches twice (clearState then the user's launchApp).
- export sibling mapping (939-941): existing folders such as en-GB, es-MX and fr-CA are silently overwritten with the base-language shots, deleting hand-made ones. The README never mentions this. Fix: document, or require `--overwrite-siblings`.

### README vs behavior
- Tips example `tapOn: { text: ... }` is not translated (finding 6).
- "Languages that failed a check are skipped": run-level failures and 0-screenshot locales are not (finding 1).
- "every language your app ships" is true on Android only (finding 7).
- Limits says Compose Multiplatform resources on iOS aren't read, but `load_strings` reads `.cvr` files (140). Either claim is stale.
- Sample output "checked 72 screenshots: 0 problem(s)" differs from the real "checked N screenshots in M languages: ..." (812).
- Exit code table says 1 means problems, but uncaught exceptions also exit 1 (finding 3).
- `strings`, `base_locale`, `timeout_s`, `avd`, `system_image` config keys are undocumented, and `base_locale` is partially ignored on Android (finding 5).
- `check` report location: README says ./shotfleet-check, but the report is written into the folder itself when it contains run.json (774).

## Checked and found fine
store_code/app_locale (round trip of every APP_STORE and PLAY code returns itself; nb/no/iw/he/zh-Hant-HK/pt-PT/es-419 map sensibly, t3.py), no `shell=True` anywhere (list-form subprocess only, so app names and paths cannot inject shell on the host; the only shell-on-device use is `adb shell ... pkg`/locale from the user's own config, low risk), html.escape in the gallery, locale names used in rmtree/export paths are always validated against known strings or store codes (no traversal).
