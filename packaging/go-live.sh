#!/bin/sh
# Launch day, in one command, once the Lemon Squeezy product exists (LAUNCH.md):
#   packaging/go-live.sh https://<store>.lemonsqueezy.com/buy/<id>
# Publishes the signed, notarized release on the site (install.sh), switches the site from waitlist to "Buy",
# deploys it, and prints the waitlist emails for the launch email.
set -eu
CHECKOUT=${1:?usage: packaging/go-live.sh <Lemon Squeezy checkout URL>}
cd "$(dirname "$0")/.."
packaging/release.sh
python3 - "$CHECKOUT" <<'PY'
import re, sys
p = "site/public/index.html"; s = open(p).read()
s = re.sub(r"    <!-- WAITLIST -->.*?<!-- /WAITLIST -->\n", "", s, flags=re.S)
s = re.sub(r"    <!-- SALE\n(.*?)\n    SALE -->", lambda m: m.group(1).replace("@CHECKOUT@", sys.argv[1]), s, flags=re.S)
s = s.replace("Early access", "Buy shotfleet")
open(p, "w").write(s)
PY
(cd site && npx --yes wrangler@latest deploy)
git add site/public/index.html && git commit -m "Site: sale open" && git push
echo; echo "Live. Waitlist to email (marketing/launch-email.md):"; site/signups.sh
