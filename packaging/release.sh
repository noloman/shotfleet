#!/bin/sh
# Publish a release on the shotfleet site: build (signed + notarized), copy it to site/public/download, deploy.
# Buyers install with: curl -fsSL https://shotfleet.manulorenzop.workers.dev/install.sh | sh
set -eu
cd "$(dirname "$0")/.."
export DEVELOPER_ID="${DEVELOPER_ID:-Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)}"
export NOTARY_PROFILE="${NOTARY_PROFILE:-KeysiNotary}"
packaging/build.sh
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
D=site/public/download; mkdir -p "$D"
cp "dist/shotfleet-$VERSION-macos-arm64.tar.gz" "$D/shotfleet-macos-arm64.tar.gz"
(cd "$D" && shasum -a 256 shotfleet-macos-arm64.tar.gz > shotfleet-macos-arm64.tar.gz.sha256)
echo "$VERSION" > "$D/VERSION"
(cd site && npx --yes wrangler@latest deploy)
echo "released $VERSION"
