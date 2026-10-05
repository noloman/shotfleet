#!/bin/sh
# Render Formula/shotfleet.rb for one TESTED release (the tarball in the publish manifest), not for whatever is on the site.
#   research/proposed-tap/render-formula.sh <version> <tarball> <url-of-that-exact-tarball> > Formula/shotfleet.rb
# The URL must be immutable (versioned). Today the site serves only /download/shotfleet-macos-arm64.tar.gz (latest), see the note.
set -eu
[ $# = 3 ] && [ -f "$2" ] || { echo "usage: render-formula.sh <version> <tarball> <url>" >&2; exit 2; }
SUM=$(shasum -a 256 "$2" | cut -d' ' -f1)
sed -e "s|@VERSION@|$1|" -e "s|@SHA256@|$SUM|" -e "s|@URL@|$3|" "$(dirname "$0")/Formula/shotfleet.rb"
