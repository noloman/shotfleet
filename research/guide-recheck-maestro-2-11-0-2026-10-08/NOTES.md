# The guide "Run one Maestro flow in every language" re-checked on Maestro 2.11.0 (2026-10-08)

The guide said "Everything here was run on Maestro 2.0.10 only". This is the re-run of its TO VERIFY items 1, 2, 3, 5, 6, 7 and 8 on 2.11.0 (`maestro --version` 2.11.0, from `~/.maestro-tests/2.11.0/bin`).

Setup: fixture apps (`tools/fixture-app`, `tools/fixture-app-android`), a private iPhone 17 simulator on iOS 26.4, two read-only copies of the `shotfleet_android` AVD (API 36) on ports 5760 and 5762, device lock held 13:31 to 13:36, Mac load about 150. The job is `job.py` (hard limits per call, 55 min cap), started by `waiter.py` under the queue rules. Result file: `summary.json`; per-run logs in `logs/`; screenshots in `images/` (the straight-after-launch image is shrunk).

| Guide item | 2.0.10 (2026-10-03) | 2.11.0 (this run) |
|---|---|---|
| `launchApp` `arguments` with `${APP_LANG}` expand (iOS) | German screen for `de` | same: "Einstellungen" and "Fertig" (`images/..133241__guide__shots__de__02_settings.png`) |
| `takeScreenshot: shots/${APP_LANG}/...` | files under the folder `maestro` was started from | the flow works, but the files are in Maestro's output folder: `<home>/.maestro/tests/<timestamp>/<flow>/takeScreenshot/shots/<lang>/`; nothing under the working directory |
| `-e` after `test` | works | works (en, de, ja) |
| `-e` before `test` | `Unknown options`, exit 2 | same message, exit 2 |
| Header `env:` default beats `-e` (trap 1) | English screen, file in `en/` | same (`images/..133318__header-default__t1__en_welcome.png`) |
| `takeScreenshot` straight after `launchApp` (iOS) | home screen, 4 of 4 | home screen, 1 of 1 (`images/..133332__race__...`) |
| Android: `set-app-locales de`, flow without `clearState` | `[de]` kept | `[de]` kept, flow passed, German screens |
| Android: flow with `clearState: true` | `[]` | `[]` (the flow then failed at the German tap, as the English screen showed) |
| Android: `pm clear` after `set-app-locales de` | `[]` | `[]` |
| `runFlow` `when: platform:` | only the matching block | only `ios_block` on iOS, only `android_block` on Android |
| Two `maestro test` processes on two emulators together (trap 4) | one of the two failed in both attempts (`TimeoutException`, `NoSuchFileException`), java listening on 7001 | 2 attempts, all 4 runs passed (rc 0), no `TimeoutException` or `NoSuchFileException`; nothing listening on 7001 10 s in (7 other java listeners) |

Not covered: `--shard-split`, versions between 2.0.10 and 2.11.0, real apps, `launchApp` `permissions`, Android permission dialogs, a loaded Mac (the first runs of the 2.0.10 note were under heavy load, this one at load about 150), and only two attempts for trap 4.
Edits made from this: the guide text (the article source `marketing/articles/02-one-maestro-flow-every-locale.md`, item 11 of its TO VERIFY list, and the published page) and claim C315.
