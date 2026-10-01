#!/bin/sh
# shotfleet installer: curl -fsSL https://shotfleet.manulorenzop.workers.dev/install.sh | sh
set -eu
BASE="${SHOTFLEET_BASE:-https://shotfleet.manulorenzop.workers.dev/download}"
[ "$(uname -s)" = Darwin ] || { echo "shotfleet runs on macOS only" >&2; exit 1; }
[ "$(uname -m)" = arm64 ] || { echo "shotfleet needs an Apple silicon Mac for now (Intel build coming)" >&2; exit 1; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz" -o "$TMP/shotfleet.tar.gz"
curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz.sha256" -o "$TMP/sum"
[ "$(shasum -a 256 "$TMP/shotfleet.tar.gz" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$TMP/sum")" ] \
  || { echo "download is corrupt (checksum mismatch); try again" >&2; exit 1; }
tar -xzf "$TMP/shotfleet.tar.gz" -C "$TMP"
for DIR in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do
  if [ -d "$DIR" ] && [ -w "$DIR" ]; then break; fi
  [ "$DIR" = "$HOME/.local/bin" ] && mkdir -p "$DIR"
done
install -m 755 "$TMP/shotfleet" "$DIR/shotfleet"
echo "installed $("$DIR/shotfleet" --version) to $DIR"
case ":$PATH:" in *":$DIR:"*) ;; *) echo "add it to your PATH: echo 'export PATH=\"$DIR:\$PATH\"' >> ~/.zshrc";; esac
echo "next: shotfleet doctor, then shotfleet activate <your key> (check is free without one)"
