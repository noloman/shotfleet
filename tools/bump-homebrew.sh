#!/bin/sh
# Point the Homebrew cask in a checkout of noloman/homebrew-tap at one released version, and print the diff.
# It reads the sha256 from the published .sha256 next to the versioned tarball, checks it against the tarball itself,
# sets version and sha256 (the cask's url is built from version), and never commits or pushes: read the diff, then commit and push yourself.
#   sh tools/bump-homebrew.sh <version> [<homebrew-tap checkout>]   (default checkout: ../homebrew-tap)
set -eu
[ $# -ge 1 ] && [ $# -le 2 ] || { echo "usage: sh tools/bump-homebrew.sh <version> [<homebrew-tap checkout>]" >&2; exit 2; }
V=$1; TAP=${2:-../homebrew-tap}; CASK="$TAP/Casks/shotfleet.rb"
echo "$V" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$' || { echo "bump-homebrew: '$V' is not a version like 0.1.4" >&2; exit 2; }
[ -f "$CASK" ] && [ -d "$TAP/.git" ] || { echo "bump-homebrew: $TAP is not a homebrew-tap checkout (no Casks/shotfleet.rb)" >&2; exit 2; }
BASE="${SHOTFLEET_BASE:-https://shotfleet.com/download}/$V"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz.sha256" -o "$TMP/sum" || { echo "bump-homebrew: no $BASE/shotfleet-macos-arm64.tar.gz.sha256 (is $V published?)" >&2; exit 1; }
curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz" -o "$TMP/t.tgz"
SUM=$(cut -d' ' -f1 "$TMP/sum")
[ "$(shasum -a 256 "$TMP/t.tgz" | cut -d' ' -f1)" = "$SUM" ] || { echo "bump-homebrew: the tarball doesn't match its .sha256" >&2; exit 1; }
sed -i '' -e "s/^  version \".*\"/  version \"$V\"/" -e "s/^  sha256 \".*\"/  sha256 \"$SUM\"/" "$CASK"
git -C "$TAP" --no-pager diff -- Casks/shotfleet.rb
echo "bump-homebrew: Casks/shotfleet.rb now says $V ($SUM); nothing committed or pushed. Check with: brew audit --new --strict --cask noloman/tap/shotfleet" >&2
