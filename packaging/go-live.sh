#!/bin/sh
# Launch day, in one command, once the Gumroad product exists (LAUNCH.md):
#   packaging/go-live.sh <Gumroad product URL> <Gumroad product ID>
# The URL is the product's page (https://<account>.gumroad.com/l/<permalink>); the ID is the one the License key block shows on the
# product's Content page while editing (22 characters ending in ==). The released program checks keys against that product.
# Publishes the signed, notarized release on the site (install.sh), switches the site from waitlist to "Buy",
# deploys it, and prints the waitlist emails for the launch email.
#
# Rehearse first (changes nothing outside a temp copy: no build, notarization, deploy or push, no network):
#   packaging/go-live.sh --dry-run <Gumroad product URL> <Gumroad product ID>
# It runs the same sed, the same site transform and the same git commits on a copy of the working tree, then prints the
# diff, checks the result, runs the claims check on it and lists what the real run would do.
# Dry-run switches: GOLIVE_DRYRUN_DIR=<dir> keeps the copy there; GOLIVE_SKIP_TESTS=1 skips the claims check on it;
# GOLIVE_SKIP_MACHINE_CHECKS=1 skips the checks of this Mac (git upstream, clean tree, tools, signing identity);
# GOLIVE_ALLOW_DIRTY=1 makes a dirty working tree a warning.
set -eu
DRY=0
if [ "${1:-}" = --dry-run ]; then DRY=1; shift; fi
CHECKOUT=${1:?usage: packaging/go-live.sh [--dry-run] <Gumroad product URL> <Gumroad product ID>}
GUMROAD_ID=${2:?usage: packaging/go-live.sh [--dry-run] <Gumroad product URL> <Gumroad product ID>}
cd "$(dirname "$0")/.."
GITOPTS=  # the dry run commits quietly

say() { if [ "$DRY" = 1 ]; then echo "  would: $*"; fi; }

if [ "$DRY" = 1 ]; then
  BAD=0
  ok() { echo "  ok    $*"; }
  warn() { echo "  WARN  $*"; }
  fail() { echo "  FAIL  $*"; BAD=1; }
  echo "== go-live DRY RUN: nothing is built, uploaded, deployed or pushed =="
  echo "-- inputs"
  case "$CHECKOUT" in
    *[[:space:]\"\'\`\$\\]*) fail "product link has spaces, quotes or other odd characters: $CHECKOUT" ;;
    https://*.gumroad.com/l/?*|https://gumroad.com/l/?*|https://gum.co/?*) ok "Gumroad product link: $CHECKOUT" ;;
    https://*) warn "product link is not a gumroad.com/l/<permalink> link: $CHECKOUT" ;;
    *) fail "product link must start with https://: $CHECKOUT" ;;
  esac
  if printf '%s' "$GUMROAD_ID" | grep -Eq '[^A-Za-z0-9_=-]|^$'; then fail "Gumroad product ID has odd characters (spaces, quotes, slashes): $GUMROAD_ID"
  elif printf '%s' "$GUMROAD_ID" | grep -Eq '^[A-Za-z0-9_-]{22}==$'; then ok "Gumroad product ID has the usual shape (22 characters and ==)"
  else warn "Gumroad product ID is not 22 characters ending in ==: $GUMROAD_ID (copy it from the License key block on the product's Content page)"; fi
  if [ "$BAD" = 1 ]; then echo "== DRY RUN FOUND PROBLEMS: do not run the real go-live yet =="; exit 1; fi  # bad inputs: nothing to rehearse
  if [ "${GOLIVE_SKIP_MACHINE_CHECKS:-}" != 1 ]; then
    echo "-- this Mac"
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then ok "branch $BRANCH pushes to $(git rev-parse --abbrev-ref --symbolic-full-name '@{u}')"
    else fail "branch $BRANCH has no upstream: the final git push would fail AFTER the site is deployed"; fi
    [ "$BRANCH" = main ] || warn "branch is $BRANCH, not main"
    if ! git diff --cached --quiet; then fail "something is staged: the go-live commits would include it"; fi
    if [ -n "$(git status --porcelain)" ]; then
      if [ "${GOLIVE_ALLOW_DIRTY:-}" = 1 ]; then warn "working tree is not clean (allowed)"; else fail "working tree is not clean: the build and the commits would include it"; fi
    else ok "working tree is clean"; fi
    for t in python3 swiftc xcrun codesign npx node shasum; do command -v "$t" >/dev/null 2>&1 && ok "$t found" || fail "$t not found"; done
    ID="${DEVELOPER_ID:-Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)}"
    if security find-identity -v -p codesigning 2>/dev/null | grep -qF "$ID"; then ok "signing identity in the keychain: $ID"; else fail "signing identity not in the keychain: $ID"; fi
    warn "not checked here (needs the network): xcrun notarytool history --keychain-profile ${NOTARY_PROFILE:-ShotfleetNotary}; (cd site && npx wrangler whoami)"
  fi
  W=${GOLIVE_DRYRUN_DIR:-$(mktemp -d)}
  mkdir -p "$W"; [ -n "${GOLIVE_DRYRUN_DIR:-}" ] || trap 'rm -rf "$W"' EXIT
  git ls-files -co --exclude-standard | tar -cf - -T - | tar -xf - -C "$W"  # what git would commit, plus today's edits
  cd "$W"
  export GIT_AUTHOR_NAME=dry-run GIT_AUTHOR_EMAIL=dry-run@localhost GIT_COMMITTER_NAME=dry-run GIT_COMMITTER_EMAIL=dry-run@localhost
  GITOPTS=-q
  git init -q && git add -A && git commit -q -m baseline
  echo "-- the copy: $W"
fi

# The two edits below are the real run's own code; the dry run executes them on the copy.
transform_site() {
python3 - "$CHECKOUT" <<'PY'
import os, re, sys
for p in ("site/public/index.html", "site/public/alternatives.html", "site/public/terms.html"):  # the pages that carry waitlist copy
    if not os.path.exists(p): continue
    s = open(p).read()
    s = re.sub(r"    <!-- WAITLIST -->.*?<!-- /WAITLIST -->\n", "", s, flags=re.S)
    s = re.sub(r"    <!-- SALE\n(.*?)\n    SALE -->", lambda m: m.group(1).replace("@CHECKOUT@", sys.argv[1]), s, flags=re.S)
    s = s.replace("Early access", "Buy shotfleet")
    open(p, "w").write(s)
PY
}

if [ "$DRY" = 0 ]; then NOTARY_PROFILE=${NOTARY_PROFILE:-ShotfleetNotary} packaging/notary-check.sh; fi  # before any edit, commit or build
# The released program checks Gumroad keys against this product (and only this one).
case "$GUMROAD_ID" in *[!A-Za-z0-9_=-]*|"") echo "go-live: the Gumroad product ID has odd characters: $GUMROAD_ID" >&2; exit 2 ;; esac
sed -i '' "s|^GUMROAD_PRODUCT_ID = .*|GUMROAD_PRODUCT_ID = \"$GUMROAD_ID\"  # set by packaging/go-live.sh|" shotfleet.py
git add shotfleet.py && { git diff --cached --quiet || git commit $GITOPTS -m "Gumroad product ID for licence checks"; }  # no-op if the ID is already there
if [ "$DRY" = 0 ]; then packaging/release.sh; fi
transform_site
if [ "$DRY" = 0 ]; then
  (cd site && npx --yes wrangler@latest deploy)
  git add site/public/index.html site/public/alternatives.html site/public/terms.html && git commit -m "Site: sale open" && git push
  echo; echo "Live. Waitlist to email (marketing/launch-email.md):"; site/signups.sh
  exit 0
fi

# ---- dry run only from here: check the copy, show what changed, list what the real run does ----
git add site/public/index.html site/public/alternatives.html site/public/terms.html && git commit -q -m "Site: sale open"
echo "-- diff of the copy against today's tree"
FIRST=$(git rev-list --max-parents=0 HEAD)
git diff --stat "$FIRST" HEAD | sed 's/^/  /'
git diff -U0 "$FIRST" HEAD -- shotfleet.py | grep '^[+-][^+-]' | sed 's/^/  /' || true
echo "  index.html: $(git diff --numstat "$FIRST" HEAD -- site/public/index.html | awk '{print "+"$1" -"$2" lines"}')"
echo "-- the transformed page"
H=site/public/index.html
N=$(grep -cF "href=\"$CHECKOUT\"" "$H" || true)
if [ "$N" -ge 3 ]; then ok "checkout link in $N places (nav, hero, price card)"; else fail "checkout link appears $N times, expected at least 3"; fi
for m in "WAITLIST" "SALE" "@CHECKOUT@" "@GUMROAD@" "data-signup" 'id="signup' "Join the list" "Early access"; do
  if grep -qF -- "$m" "$H"; then fail "page still contains: $m"; else ok "no $m"; fi
done
for o in site/public/alternatives.html site/public/terms.html; do
  if grep -qE "WAITLIST|SALE|@CHECKOUT@|not on sale yet|join the waitlist" "$o"; then fail "$o still has waitlist copy or markers"; else ok "$o: no waitlist copy, no markers"; fi
done
grep -qF "first 100 buyers" "$H" && ok 'founder price text is static: "first 100 buyers" (no counter number)' || fail "the page lost its 'first 100 buyers' text"
if grep -Eiq '[0-9]+ (of 100|left|remaining)|spots? left' "$H"; then fail "page shows a counter number that nothing feeds"; else ok "no counter number on the page"; fi
[ "$(grep -cF 'curl -fsSL https://shotfleet.com/install.sh | sh' "$H")" = 1 ] && ok "install line appears once" || fail "install line count is not 1"
python3 -m py_compile shotfleet.py && ok "shotfleet.py compiles" || fail "shotfleet.py does not compile"
rm -rf __pycache__
grep -qF "GUMROAD_PRODUCT_ID = \"$GUMROAD_ID\"" shotfleet.py && ok "GUMROAD_PRODUCT_ID line set" || fail "GUMROAD_PRODUCT_ID line not set"
python3 - "$GUMROAD_ID" <<'PY' && ok "shotfleet.py imports and holds the product ID" || fail "shotfleet.py does not import, or does not hold the product ID"
import sys, shotfleet as sf
assert sf.GUMROAD_PRODUCT_ID == sys.argv[1]
PY
rm -rf __pycache__
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
if [ "${GOLIVE_SKIP_TESTS:-}" = 1 ]; then warn "claims check on the copy skipped (GOLIVE_SKIP_TESTS=1)"
else
  echo "-- claims check on the copy (the state the real run would deploy)"
  if SHOTFLEET_DRYRUN=1 tools/check-claims.sh >"$W/claims.log" 2>&1; then ok "$(tail -1 "$W/claims.log")"; else cat "$W/claims.log"; fail "claims check fails on the transformed copy"; fi
  rm -f "$W/claims.log"
fi
echo "-- the real run would, in this order"
say "1. sed GUMROAD_PRODUCT_ID in shotfleet.py to $GUMROAD_ID and commit \"Gumroad product ID for licence checks\""
say "2. (nothing: Gumroad needs no other edit in the program; keys check against api.gumroad.com with that product ID)"
say "3. packaging/release.sh: tools/check-claims.sh, build $VERSION (sign with DEVELOPER_ID, notarize with ${NOTARY_PROFILE:-ShotfleetNotary}), copy to site/public/download, write VERSION, wrangler deploy (first deploy: still the waitlist page)"
say "4. transform site/public/index.html (drop WAITLIST blocks, open SALE blocks with $CHECKOUT, Early access -> Buy shotfleet)"
say "5. (cd site && npx wrangler deploy): the sale page goes live on shotfleet.com"
say "6. commit \"Site: sale open\" and git push (needs the upstream the check above found)"
say "7. site/signups.sh: print the waitlist emails for marketing/launch-email.md"
echo "after step 5, run: tools/golive/smoke.sh https://shotfleet.com $CHECKOUT"
echo "and before step 3 (it reads the live Gumroad product page): tools/golive/storefront.sh $CHECKOUT $GUMROAD_ID"
[ -n "${GOLIVE_DRYRUN_DIR:-}" ] && echo "copy kept in $W"
if [ "$BAD" = 1 ]; then echo "== DRY RUN FOUND PROBLEMS: do not run the real go-live yet =="; exit 1; fi
echo "== dry run clean: nothing was built, deployed or pushed =="
