#!/bin/sh
# Build the Android fixture app with the SDK's own tools only (no Gradle, no downloads): tools/fixture-app-android/build.sh [output dir]
# -> <dir>/FleetFixture.apk, package com.shotfleet.fixture, minSdk 33, en/de/ja/ar/tr. Signed with a throwaway debug key made in <dir>.
# Needs: ANDROID_HOME (default ~/Library/Android/sdk) with build-tools (aapt2, d8, zipalign, apksigner) and a platform android.jar, and a JDK.
set -eu
cd "$(dirname "$0")"
SDK=${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$HOME/Library/Android/sdk}}
OUT=${1:-build}; mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd); W=$OUT/work; APK=$OUT/FleetFixture.apk
# newest build-tools that has all four tools, newest numbered platform that has an android.jar
BT=$(for d in "$SDK"/build-tools/*/; do [ -x "$d/aapt2" ] && [ -x "$d/d8" ] && [ -x "$d/zipalign" ] && [ -x "$d/apksigner" ] && echo "${d%/}"; done | sort -V | tail -1)
JAR=$(for d in "$SDK"/platforms/android-[0-9]*; do [ -f "$d/android.jar" ] && echo "$d/android.jar"; done | grep -E 'android-[0-9]+/' | sort -t- -k2 -n | tail -1)
[ -n "$BT" ] && [ -n "$JAR" ] || { echo "build.sh: no usable build-tools or platform android.jar under $SDK" >&2; exit 1; }
rm -rf "$W" "$APK" && mkdir -p "$W/gen" "$W/classes" "$W/dex"
"$BT/aapt2" compile --dir res -o "$W/res.zip"
"$BT/aapt2" link -o "$W/base.apk" -I "$JAR" --manifest AndroidManifest.xml --min-sdk-version 33 --target-sdk-version 34 --java "$W/gen" "$W/res.zip"
javac --release 17 -classpath "$JAR" -d "$W/classes" "$W/gen/com/shotfleet/fixture/R.java" src/com/shotfleet/fixture/MainActivity.java
"$BT/d8" --min-api 33 --lib "$JAR" --output "$W/dex" $(find "$W/classes" -name '*.class')
(cd "$W/dex" && zip -q -j "$W/base.apk" classes.dex)
"$BT/zipalign" -f -p 4 "$W/base.apk" "$W/aligned.apk"
keytool -genkeypair -keystore "$W/debug.keystore" -storepass android -keypass android -alias fixture -keyalg RSA -keysize 2048 -validity 3650 -dname "CN=shotfleet fixture" >/dev/null 2>&1
"$BT/apksigner" sign --ks "$W/debug.keystore" --ks-pass pass:android --key-pass pass:android --out "$APK" "$W/aligned.apk"
rm -rf "$W" "$APK.idsig"
echo "built $APK"
