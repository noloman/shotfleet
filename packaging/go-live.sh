#!/bin/sh
# Launch day, in one command, once the Polar product exists (LAUNCH.md):
#   POLAR_ORG_ID=<organization id> packaging/go-live.sh <Polar checkout link>
# Publishes the signed, notarized release on the site (install.sh), switches the site from waitlist to "Buy",
# deploys it, and prints the waitlist emails for the launch email.
set -eu
CHECKOUT=${1:?usage: POLAR_ORG_ID=<id> packaging/go-live.sh <checkout URL> [<Gumroad product URL> <Gumroad product ID>]}
GUMROAD_URL=${2:-}; GUMROAD_ID=${3:-}
cd "$(dirname "$0")/.."
if [ -n "${POLAR_ORG_ID:-}" ]; then  # the released program checks Polar keys against this organization
  sed -i '' "s/^POLAR_ORG_ID = .*/POLAR_ORG_ID = \"$POLAR_ORG_ID\"  # set by packaging\/go-live.sh/" shotfleet.py
  git add shotfleet.py && git commit -m "Polar organization ID for licence checks"
fi
if [ -n "$GUMROAD_URL" ]; then  # the released program checks Gumroad keys against this product
  : "${GUMROAD_ID:?a Gumroad product URL needs the product ID too (LAUNCH.md step 2)}"
  sed -i '' "s/^GUMROAD_PRODUCT_ID = .*/GUMROAD_PRODUCT_ID = \"$GUMROAD_ID\"  # set by packaging\/go-live.sh/" shotfleet.py
  git add shotfleet.py && git commit -m "Gumroad product ID for licence checks"
fi
packaging/release.sh
python3 - "$CHECKOUT" "$GUMROAD_URL" <<'PY'
import re, sys
p = "site/public/index.html"; s = open(p).read()
s = re.sub(r"    <!-- WAITLIST -->.*?<!-- /WAITLIST -->\n", "", s, flags=re.S)
def sale(m):
    block = m.group(1).replace("@CHECKOUT@", sys.argv[1])
    if sys.argv[2]: return block.replace("@GUMROAD@", sys.argv[2])
    return "\n".join(l for l in block.splitlines() if "data-gumroad" not in l)
s = re.sub(r"    <!-- SALE\n(.*?)\n    SALE -->", sale, s, flags=re.S)
s = s.replace("Early access", "Buy shotfleet")
open(p, "w").write(s)
PY
(cd site && npx --yes wrangler@latest deploy)
git add site/public/index.html && git commit -m "Site: sale open" && git push
echo; echo "Live. Waitlist to email (marketing/launch-email.md):"; site/signups.sh
