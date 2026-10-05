#!/bin/sh
# Publish a release on the shotfleet site: build (signed + notarized), copy it to site/public/download, deploy.
# Buyers install with: curl -fsSL https://shotfleet.com/install.sh | sh
# NOTE (0.1.2): this builds AND deploys in one run, so it ships different bytes than it tested. Used once, by go-live.sh. For later releases use
# packaging/build.sh, test those files, then packaging/publish.sh (see packaging/README.md).
set -eu
cd "$(dirname "$0")/.."
export DEVELOPER_ID="${DEVELOPER_ID:-Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)}"
export NOTARY_PROFILE="${NOTARY_PROFILE:-ShotfleetNotary}"
packaging/notary-check.sh
tools/check-claims.sh || { echo "release gate: the claims and tests must pass before a release" >&2; exit 1; }
export INSTALLER_ID="${INSTALLER_ID:-Developer ID Installer: Manuel Lorenzo Parejo (2357A78TMR)}"
packaging/build.sh
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
D=site/public/download; mkdir -p "$D"
cp "dist/shotfleet-$VERSION-macos-arm64.tar.gz" "$D/shotfleet-macos-arm64.tar.gz"
(cd "$D" && shasum -a 256 shotfleet-macos-arm64.tar.gz > shotfleet-macos-arm64.tar.gz.sha256)
cp "dist/shotfleet-$VERSION-macos-arm64.pkg" "$D/shotfleet-macos-arm64.pkg"
echo "$VERSION" > "$D/VERSION"
(cd site && npx --yes wrangler@latest deploy)
echo "released $VERSION"
