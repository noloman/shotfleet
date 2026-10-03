#!/bin/sh
# Build the fixture app for the iOS Simulator (arm64): tools/fixture-app/build.sh [output dir]
# -> <dir>/FleetFixture.app, bundle id dev.shotfleet.fixture, iPhone and iPad, en/de/ja/ar/tr.
set -eu
cd "$(dirname "$0")"
OUT=${1:-build}; APP="$OUT/FleetFixture.app"
rm -rf "$APP" && mkdir -p "$APP"
xcrun -sdk iphonesimulator swiftc -parse-as-library -O -target arm64-apple-ios17.0-simulator App.swift -o "$APP/FleetFixture"
for d in Resources/*.lproj; do cp -R "$d" "$APP/"; done
cat > "$APP/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleIdentifier</key><string>dev.shotfleet.fixture</string>
  <key>CFBundleName</key><string>FleetFixture</string>
  <key>CFBundleDisplayName</key><string>Fleet Fixture</string>
  <key>CFBundleExecutable</key><string>FleetFixture</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundleVersion</key><string>1</string>
  <key>CFBundleDevelopmentRegion</key><string>en</string>
  <key>CFBundleLocalizations</key><array><string>en</string><string>de</string><string>ja</string><string>ar</string><string>tr</string></array>
  <key>CFBundleSupportedPlatforms</key><array><string>iPhoneSimulator</string></array>
  <key>DTPlatformName</key><string>iphonesimulator</string>
  <key>MinimumOSVersion</key><string>17.0</string>
  <key>UIDeviceFamily</key><array><integer>1</integer><integer>2</integer></array>
  <key>UILaunchScreen</key><dict/>
  <key>UISupportedInterfaceOrientations</key><array><string>UIInterfaceOrientationPortrait</string></array>
  <key>UISupportedInterfaceOrientations~ipad</key><array><string>UIInterfaceOrientationPortrait</string><string>UIInterfaceOrientationPortraitUpsideDown</string><string>UIInterfaceOrientationLandscapeLeft</string><string>UIInterfaceOrientationLandscapeRight</string></array>
</dict></plist>
PLIST
codesign --force --sign - "$APP"
echo "built $APP"
