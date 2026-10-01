#!/bin/sh
# Publish a release: build (signed + notarized when DEVELOPER_ID/NOTARY_PROFILE are set), upload the tarball to
# noloman/shotfleet-releases, and point the Homebrew tap at it. Needs both public repos to exist.
set -eu
cd "$(dirname "$0")/.."
packaging/build.sh
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
TAR="dist/shotfleet-$VERSION-macos-arm64.tar.gz"
SHA=$(shasum -a 256 "$TAR" | cut -d' ' -f1)
gh release create "v$VERSION" "$TAR" --repo noloman/shotfleet-releases --title "shotfleet $VERSION" --notes-file CHANGELOG.md
TAP=$(mktemp -d)
gh repo clone noloman/homebrew-shotfleet "$TAP"
mkdir -p "$TAP/Formula"
sed -e "s/@VERSION@/$VERSION/g" -e "s/@SHA256@/$SHA/" packaging/shotfleet.rb > "$TAP/Formula/shotfleet.rb"
git -C "$TAP" add Formula/shotfleet.rb
git -C "$TAP" commit -m "shotfleet $VERSION"
git -C "$TAP" push
echo "released $VERSION: brew install noloman/shotfleet/shotfleet"
