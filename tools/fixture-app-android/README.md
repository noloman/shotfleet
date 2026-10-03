# Android fixture app

The Android twin of `tools/fixture-app`: a tiny native-Views app (no AndroidX, no Gradle) with the same two screens and the
same words in en, de, ja, ar (right to left) and tr. "Welcome" with a "Next" button, then "Settings" with a "Done" button; in
German the buttons say "Weiter" and "Fertig". The strings in `res/values*/strings.xml` are copied word for word from
`tools/fixture-app/Resources/*.lproj`.

```sh
tools/fixture-app-android/build.sh /tmp/fixture-android     # -> /tmp/fixture-android/FleetFixture.apk (package com.shotfleet.fixture, minSdk 33)
shotfleet init /tmp/fixture-android/FleetFixture.apk --dir /tmp/e2e-android
```

`build.sh` uses only what is already in the Android SDK (`ANDROID_HOME`, default `~/Library/Android/sdk`): `aapt2`, `d8`,
`zipalign`, `apksigner` from the newest build-tools, the newest platform's `android.jar`, and the JDK's `javac` and `keytool`
(a throwaway debug keystore is generated in the output folder). No downloads.

`tools/fixture-e2e.sh --android` runs it on the phone emulator (AVD `shotfleet_android`); see the header of that script.
