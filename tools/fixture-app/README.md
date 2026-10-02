# Fixture app

A tiny SwiftUI app (two screens, iPhone and iPad, strings in en, de, ja, ar and tr) for testing shotfleet end to end
without depending on anyone's real app, whose builds come and go.

```sh
tools/fixture-app/build.sh /tmp/fixture            # -> /tmp/fixture/FleetFixture.app (bundle id dev.shotfleet.fixture)
shotfleet init /tmp/fixture/FleetFixture.app --dir /tmp/e2e
```

The flow `Next` / `Done` buttons and titles come from `Resources/<lang>.lproj/Localizable.strings` (English text as the
key, as in most SwiftUI apps), so a screenshot in German must show "Willkommen" and "Weiter".
