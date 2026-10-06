#!/bin/sh
# Read-only: fail fast when the notarytool keychain profile does not work (needs the network). Runs before any build and
# again right before each `notarytool submit` (build.sh, pkg.sh), because a release can outlive a screen lock.
#   NOTARY_PROFILE=ShotfleetNotary packaging/notary-check.sh
# notarytool keeps the profile in the data protection keychain, which locks about 5 minutes after the screen locks. It then
# says "No Keychain password item found", the same text as for a missing profile (research/notary-profile-2026-10-06.md).
NOTARY_PROFILE=${NOTARY_PROFILE:-ShotfleetNotary}
OUT=$(perl -e 'alarm 60; exec @ARGV' xcrun notarytool history --keychain-profile "$NOTARY_PROFILE" 2>&1) && exit 0
echo "notary check: 'xcrun notarytool history --keychain-profile $NOTARY_PROFILE' failed: $(printf '%s\n' "$OUT" | grep -iv 'token' | grep . | head -1 | cut -c1-160)" >&2
case "$OUT" in
  *"No Keychain password item found"*)
    # ponytail: always names the lock; a log query for lock events takes ~13 s and cannot tell a lock from a missing profile anyway
    echo "macOS locks this keychain about 5 minutes after the screen locks. Unlock the Mac and run again." >&2
    echo "Only if it still fails: xcrun notarytool store-credentials $NOTARY_PROFILE --apple-id <your Apple ID> --team-id 2357A78TMR" >&2
    echo "(store-credentials asks for the app-specific password; never paste it into a command line or a chat.)" >&2 ;;
  *) echo "No network, or Apple is down: retry later. If the profile is missing: xcrun notarytool store-credentials $NOTARY_PROFILE --apple-id <your Apple ID> --team-id 2357A78TMR" >&2 ;;
esac
echo "Nothing was submitted to Apple." >&2
exit 1
