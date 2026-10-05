#!/bin/sh
# Build the installer package from dist/shotfleet (run packaging/build.sh first): signed, notarized, ticket stapled.
#   INSTALLER_ID="Developer ID Installer: Name (TEAMID)" NOTARY_PROFILE=<xcrun notarytool store-credentials name> packaging/pkg.sh
# Why a package: files the macOS Installer lays down carry no quarantine flag, so Gatekeeper never checks the program when it
# runs. A bare executable from a browser download cannot have a ticket stapled: it is checked online at first run, and a Finder
# double-click or an offline Mac shows "Apple could not verify ...". Without NOTARY_PROFILE the package is only signed.
set -eu
cd "$(dirname "$0")/.."
notary_failed() {  # $1: the notarytool log; name the submission id only when Apple gave one
  ID=$(sed -n 's/^ *id: //p' "$1" | head -1)
  if [ -n "$ID" ]; then echo "pkg: notarization failed: xcrun notarytool log $ID --keychain-profile $NOTARY_PROFILE" >&2
  else echo "pkg: notarization failed before Apple gave a submission id (notarytool's message is above; check the profile: packaging/notary-check.sh)" >&2; fi
  exit 1
}
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
PKG="dist/shotfleet-$VERSION-macos-$(uname -m).pkg"
[ -x dist/shotfleet/shotfleet ] || { echo "pkg: no dist/shotfleet; run packaging/build.sh first" >&2; exit 1; }
: "${INSTALLER_ID:?pkg: set INSTALLER_ID to the Developer ID Installer certificate name}"
STAGE=$(mktemp -d); trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/root/usr/local/lib" "$STAGE/scripts" build
ditto dist/shotfleet "$STAGE/root/usr/local/lib/shotfleet"
cat > "$STAGE/scripts/postinstall" <<'EOF'
#!/bin/sh
mkdir -p /usr/local/bin && ln -sf /usr/local/lib/shotfleet/shotfleet /usr/local/bin/shotfleet
exit 0
EOF
chmod +x "$STAGE/scripts/postinstall"
rm -f "$PKG"
pkgbuild --root "$STAGE/root" --scripts "$STAGE/scripts" --identifier com.shotfleet.cli --version "$VERSION" \
  --install-location / --sign "$INSTALLER_ID" --timestamp "$PKG"
pkgutil --check-signature "$PKG" | grep -q "Developer ID Installer" || { echo "pkg: the package is not signed with a Developer ID Installer certificate" >&2; exit 1; }
if [ -n "${NOTARY_PROFILE:-}" ]; then
  (set -o pipefail; xcrun notarytool submit "$PKG" --keychain-profile "$NOTARY_PROFILE" --wait | tee build/notary-pkg.log) \
    || notary_failed build/notary-pkg.log  # pipefail only here: tee must not hide notarytool's exit status
  grep -q "status: Accepted" build/notary-pkg.log || notary_failed build/notary-pkg.log
  xcrun stapler staple "$PKG"
  xcrun stapler validate "$PKG"
  # Gatekeeper's verdict for an installer package (a bare executable cannot be assessed this way, a package can).
  spctl --assess --type install -vv "$PKG" 2>&1 | tee build/spctl-pkg.log
  grep -q "source=Notarized Developer ID" build/spctl-pkg.log || { echo "pkg: Gatekeeper does not accept the package as notarized (build/spctl-pkg.log): do not publish" >&2; exit 1; }
fi
shasum -a 256 "$PKG"
