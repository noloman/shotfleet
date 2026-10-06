# Fixture app

A tiny SwiftUI app (two screens, iPhone and iPad, strings in en, de, ja, ar and tr) for testing shotfleet end to end
without depending on anyone's real app, whose builds come and go.

```sh
tools/fixture-app/build.sh /tmp/fixture            # -> /tmp/fixture/FleetFixture.app (bundle id dev.shotfleet.fixture)
shotfleet init /tmp/fixture/FleetFixture.app --dir /tmp/e2e
```

The flow `Next` / `Done` buttons and titles come from `Resources/<lang>.lproj/Localizable.strings` (English text as the
key, as in most SwiftUI apps), so a screenshot in German must show "Willkommen" and "Weiter".

## End-to-end script

`tools/fixture-e2e.sh` builds this app and drives shotfleet through it on real simulators: `init`, `doctor`, `run` (iPhone and
iPad, de/ja/ar/tr), `check`, `export --fastlane`, then plants a copied screenshot and a missing one and expects `check` to
catch both. It prints one PASS/FAIL line per assertion and exits 0 only if all pass. It boots simulators, so it refuses to
run without the opt-in, and it wants a quiet Mac (5 GB free, memory pressure not critical):

```sh
SHOTFLEET_E2E=1 tools/fixture-e2e.sh            # about 10 minutes; --keep keeps the temp dir, --skip-android is accepted
```

`init` gets the built `.app` explicitly (its no-argument mode finds Xcode and Gradle builds only). Android is skipped: there
is no Android fixture yet. `python3 -m unittest tests.test_fixture_e2e` tests the script against fakes, with no devices.

## XCUITest target (bring your own capture)

`project.yml` describes the same app as an Xcode project with a UI test target, `UITests/ScreenshotTests.swift`: the kind of
screenshot tests a team already has (XCTAttachment with `.keepAlways`, a SnapshotHelper-style writer to fastlane's cache
folder, and a test that forgets `.keepAlways`). `FleetFixture.xcodeproj` is generated from it with `xcodegen` and committed.
`tools/fixture-byoc-e2e.sh` runs them through `shotfleet run` with a `[capture]` config on 2 simulators (de, ja). It boots
simulators, so it needs the same opt-in and a quiet Mac:

```sh
SHOTFLEET_E2E=1 tools/fixture-byoc-e2e.sh       # about 5 minutes, stopped after 30 at the latest
```
