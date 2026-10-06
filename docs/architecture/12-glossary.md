# 12. Glossary

Back to the [index](../ARCHITECTURE.md).

| Term | Meaning |
|---|---|
| **Activation** | one count on a Gumroad key's `uses` counter, made by `shotfleet activate` on a Mac that did not hold the key. A lifetime counter, not a Mac count. |
| **ANECompilerService** | the root macOS service that compiles Vision's text model on first use; the cause of "text recognition isn't answering". |
| **App text / app's own text** | the labels read from the running app's accessibility tree or Maestro's saved hierarchy, stored as `<shot>.texts.json`. Exact, any script. |
| **Base locale** | the language the flow is written in (default `en`); `base_locale` in the config. |
| **BYOC** | bring your own capture: `[capture]` runs the team's XCUITest tests instead of a Maestro flow (iOS). |
| **Budget (OCR)** | the 480 s all of a check's waiting on Vision shares (`OCR_BUDGET_S`). |
| **Capture** | everything up to PNG files in `out/raw/<locale>/`. |
| **Claim / claims register** | a public promise and its proof, one row of `tests/claims.json`. |
| **Collision** | two English labels that translate to the same word in one language, so a tap could hit the wrong one. |
| **CVR** | Compose Multiplatform resource file (`string|key|base64`). |
| **Demo mode** | Android SystemUI demo mode (fixed clock, full battery, no notifications) applied to emulators. |
| **Device lock** | the `flock` on `/tmp/shotfleet-<key>.lock` that stops two runs sharing devices; also the agent-level `mkdir` lock in `docs/device-queue.md`. |
| **Evidence** | where a screenshot's text came from in `check.json`: `hierarchy` (the app) or `ocr`. Also a claim status. |
| **Export** | copying passing languages into fastlane's folders. |
| **Fail** | the exception class for user-facing errors; ends as `shotfleet: <message>`, exit 2. |
| **Flow** | the Maestro YAML script. |
| **Free tier** | `run` capturing 2 languages without a licence. |
| **Frozen** | a PyInstaller build (`sys.frozen`); the only place the licence is enforced. |
| **Gate** | the local pre-release checks: `check-claims.sh`, proofs, the device e2e on the built files. |
| **Hierarchy marker** | the optional failing `assertTrue` after each Android `takeScreenshot` that makes Maestro 2.7+ save the screen hierarchy. |
| **Hook** | a user command in `[hooks]` run around `run` and `export`. |
| **Locale / lproj** | a language code as the app spells it (`de`, `pt-BR`, `zh-Hans`); `lproj` is the iOS folder name. `canon()` normalises them. |
| **Maestro** | the open-source mobile UI test runner shotfleet drives. Needs Java 17+. |
| **Manifest** | the file `publish.sh --make-manifest` writes with version, size and sha256 of the tested files. |
| **minos** | a Mach-O file's minimum macOS version, read by `tools/macho-minos.py`. |
| **Not verified / unverified** | a screenshot nobody could read because text recognition was busy and no other reader existed; listed, not a failure unless `--strict`. |
| **Notary profile** | the notarytool keychain profile (`ShotfleetNotary`); locked while the screen is locked. |
| **OCR** | text recognition: Vision on a Mac, Tesseract elsewhere. |
| **Override** | `[overrides.<locale>]`: what to tap for an English text in one language. |
| **Pool** | the simulators named `shotfleet-<device>-N` or the emulators on ports 5702, 5704, ... |
| **`ponytail:`** | a code comment marking a deliberate shortcut and its ceiling. |
| **Problem / note** | a failing line versus an informational line in `check.json`. |
| **Release dir** | `SHOTFLEET_RELEASE_DIR`: durable folder with `archive/` and `state/` for publishing. |
| **Rollback id** | the live Cloudflare version id recorded before a deploy. |
| **Round** | one Android pass: one language per emulator. |
| **Shard (`--shard-split`)** | Maestro's way to run several flows at once on several devices from one process. |
| **Shipped locales** | the languages the app itself translates, excluding libraries' (`shipped_locales`). |
| **Snapshot (emulator)** | the saved `shotfleet` boot state read-only emulators start from. |
| **SnapshotHelper** | fastlane's Swift helper that writes screenshots to `~/Library/Caches/tools.fastlane/screenshots`. |
| **Stall watchdog** | kills Maestro when no new screenshot appears for `stall_s` (default 900). |
| **Store code** | a listing folder name of fastlane (`de-DE`, `zh-Hans`, `es-419`). |
| **Table** | a locale's normalised strings plus its format regex, used by `judge_screen`. |
| **Texts.json** | `<shot>.texts.json`, the app text for one screenshot. |
| **Twins** | language pairs detection cannot separate (`ms`/`id`, `hr`/`sl`). |
| **Update window** | the planned "a year of updates" enforcement (0.1.6 branch). |
| **Versioned downloads** | permanent `/download/<version>/` files, immutable. |
| **Vision** | Apple's text recognition framework, used through `ocr.swift`. |
| **XCUITest / xctestrun** | Apple's UI test framework / the file describing a prebuilt test run. |
