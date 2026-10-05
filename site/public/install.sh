#!/bin/sh
# shotfleet installer: curl -fsSL https://shotfleet.com/install.sh | sh
set -eu
BASE="${SHOTFLEET_BASE:-https://shotfleet.com/download}"
[ "$(uname -s)" = Darwin ] || { echo "shotfleet runs on macOS only" >&2; exit 1; }
[ "$(uname -m)" = arm64 ] || { echo "shotfleet needs an Apple silicon Mac (M1 or newer)" >&2; exit 1; }
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz" -o "$TMP/shotfleet.tar.gz"
curl -fsSL "$BASE/shotfleet-macos-arm64.tar.gz.sha256" -o "$TMP/sum"
[ "$(shasum -a 256 "$TMP/shotfleet.tar.gz" | cut -d' ' -f1)" = "$(cut -d' ' -f1 "$TMP/sum")" ] \
  || { echo "download is corrupt (checksum mismatch); try again" >&2; exit 1; }
tar -xzf "$TMP/shotfleet.tar.gz" -C "$TMP"
APP="$HOME/Library/Application Support/shotfleet/app"  # the program folder; a link to it goes on the PATH
rm -rf "$APP" && mkdir -p "$(dirname "$APP")" && mv "$TMP/shotfleet" "$APP"
for DIR in /opt/homebrew/bin /usr/local/bin "$HOME/.local/bin"; do
  if [ -d "$DIR" ] && [ -w "$DIR" ]; then break; fi
  [ "$DIR" = "$HOME/.local/bin" ] && mkdir -p "$DIR"
done
ln -sf "$APP/shotfleet" "$DIR/shotfleet"
echo "installed $("$DIR/shotfleet" --version) to $DIR"
case ":$PATH:" in *":$DIR:"*) ;; *) echo "add it to your PATH: echo 'export PATH=\"$DIR:\$PATH\"' >> ~/.zshrc, then open a new Terminal window (until you do, \"shotfleet\" is not found)";; esac
echo "next: shotfleet doctor (add --fix to fetch Maestro and Java), then shotfleet init in your app's folder. Your key: shotfleet activate <key> (check is free without one)"
