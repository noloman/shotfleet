#!/bin/sh
# Read-only check of the live Gumroad product, before go-live and any time after:
#   tools/golive/storefront.sh <Gumroad product URL> <Gumroad product ID> [<list price, e.g. 49>]
# Gumroad embeds the product's data in the page; the three settings that break a sale silently are all in it (Keysi's launch
# found each of them wrong): the product is unpublished, licence keys are off (the buyer pays and gets no key), no refund policy
# is set while the site promises 14 days. It also asks api.gumroad.com to verify a made-up key (that changes nothing).
# SHOTFLEET_GUMROAD_API overrides the API base (the tests point it at a local server).
PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH; export PATH
URL=${1:?usage: tools/golive/storefront.sh <Gumroad product URL> <Gumroad product ID> [<list price>]}
ID=${2:?usage: tools/golive/storefront.sh <Gumroad product URL> <Gumroad product ID> [<list price>]}
PRICE=${3:-}
API=${SHOTFLEET_GUMROAD_API:-https://api.gumroad.com/v2/licenses}
cd "$(dirname "$0")/../.." || exit 1
BAD=0
ok() { echo "  ok    $*"; }
fail() { echo "  FAIL  $*"; BAD=1; }
PAGE=$(curl -sSL --max-time 20 "$URL" 2>/dev/null | sed 's/&quot;/"/g') || PAGE=
if [ -z "$PAGE" ]; then fail "could not fetch $URL"; echo "storefront: FAILED"; exit 1; fi
has() { printf '%s' "$PAGE" | grep -q "$1"; }
if has '"is_published":true'; then ok "the product is published"
elif has '"is_published":false'; then fail "the product is UNPUBLISHED: the buy button leads to a page with nothing to click"
else fail 'no "is_published" field on the page: Gumroad changed the page, update this script'; fi
if has '"is_licensed":true'; then ok "licence keys are on"
else fail "licence keys are OFF (or unreadable): buyers pay and get no key. Content page, Insert, License key"; fi
if printf '%s' "$PAGE" | grep -qF "$ID"; then ok "the page carries product ID $ID"
else fail "product ID $ID is not on the page: every activation would answer 'That license does not exist for the provided product.'"; fi
if has '"refund_policy":null'; then fail "the product has NO refund policy: the site promises 14 days"
else
  TITLE=$(printf '%s' "$PAGE" | grep -oE '"refund_policy":\{"title":"[^"]*"' | head -1 | sed -E 's/.*"title":"([^"]*)"/\1/')
  case "$TITLE" in
    14*) ok "refund policy: $TITLE" ;;
    "") fail "a refund policy field exists but its title is unreadable: check the product page by eye" ;;
    *) fail "refund policy says \"$TITLE\" but the site promises 14 days: they must agree" ;;
  esac
fi
if [ -n "$PRICE" ]; then
  GOT=$(printf '%s' "$PAGE" | grep -oE '"price":[0-9.]+' | head -1 | cut -d: -f2)
  if [ "$GOT" = "$PRICE" ] || [ "$GOT" = "$PRICE.0" ] || [ "$GOT" = "$PRICE.00" ]; then ok "list price is $GOT"; else fail "list price on the page is '${GOT:-none}', expected $PRICE"; fi
fi
ANS=$(curl -sS --max-time 20 -X POST "$API/verify" --data-urlencode "product_id=$ID" --data-urlencode "license_key=00000000-00000000-00000000-00000000" \
      --data-urlencode "increment_uses_count=false" 2>/dev/null)
if printf '%s' "$ANS" | grep -q '"success":false'; then ok "licenses/verify answers and rejects a made-up key"; else fail "licenses/verify did not answer success:false: ${ANS:-nothing}"; fi
if [ "$BAD" = 0 ]; then echo "storefront: ok"; else echo "storefront: FAILED"; exit 1; fi
