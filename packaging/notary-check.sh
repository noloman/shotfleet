#!/bin/sh
# Read-only: fail fast, before any build, when the notarytool keychain profile is missing or does not work (needs the network).
#   NOTARY_PROFILE=ShotfleetNotary packaging/notary-check.sh
# The profile has vanished from the login keychain before (KeysiNotary: 2026-09-11, 2026-10-03, 2026-10-05); only the owner can recreate it.
NOTARY_PROFILE=${NOTARY_PROFILE:-ShotfleetNotary}
OUT=$(perl -e 'alarm 60; exec @ARGV' xcrun notarytool history --keychain-profile "$NOTARY_PROFILE" 2>&1) && exit 0
echo "notary check: 'xcrun notarytool history --keychain-profile $NOTARY_PROFILE' failed: $(printf '%s\n' "$OUT" | grep -iv 'token' | grep . | head -1 | cut -c1-160)" >&2
echo "If the profile is missing, the owner recreates it (it prompts for the app-specific password; never paste it into a command line or a chat):" >&2
echo "  xcrun notarytool store-credentials $NOTARY_PROFILE --apple-id <id> --team-id 2357A78TMR" >&2
echo "No network, or Apple down: retry later. Nothing was built." >&2
exit 1
