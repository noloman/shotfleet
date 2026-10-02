#!/bin/sh
# Launch day, in one command, once the Polar product exists (LAUNCH.md):
#   POLAR_ORG_ID=<organization id> packaging/go-live.sh <Polar checkout link>
# Publishes the signed, notarized release on the site (install.sh), switches the site from waitlist to "Buy",
# deploys it, and prints the waitlist emails for the launch email.
#
# Rehearse first (changes nothing outside a temp copy: no build, notarization, deploy or push, no network):
#   POLAR_ORG_ID=<organization id> packaging/go-live.sh --dry-run <Polar checkout link>
# It runs the same sed, the same site transform and the same git commits on a copy of the working tree, then prints the
# diff, checks the result, runs the claims check on it and lists what the real run would do.
# Dry-run switches: GOLIVE_DRYRUN_DIR=<dir> keeps the copy there; GOLIVE_SKIP_TESTS=1 skips the claims check on it;
# GOLIVE_SKIP_MACHINE_CHECKS=1 skips the checks of this Mac (git upstream, clean tree, tools, signing identity);
# GOLIVE_ALLOW_DIRTY=1 makes a dirty working tree a warning.
set -eu
DRY=0
if [ "${1:-}" = --dry-run ]; then DRY=1; shift; fi
CHECKOUT=${1:?usage: POLAR_ORG_ID=<id> packaging/go-live.sh [--dry-run] <checkout URL> [<Gumroad product URL> <Gumroad product ID>]}
GUMROAD_URL=${2:-}; GUMROAD_ID=${3:-}
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
    *[[:space:]\"\'\`\$\\]*) fail "checkout link has spaces, quotes or other odd characters: $CHECKOUT" ;;
    https://*.polar.sh/*|https://polar.sh/*) ok "checkout link: $CHECKOUT" ;;
    https://*) warn "checkout link is not on polar.sh: $CHECKOUT" ;;
    *) fail "checkout link must start with https://: $CHECKOUT" ;;
  esac
  if [ -n "${POLAR_ORG_ID:-}" ]; then
    case "$POLAR_ORG_ID" in
      [0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f]-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ok "POLAR_ORG_ID is a UUID" ;;
      *) fail "POLAR_ORG_ID is not a UUID: $POLAR_ORG_ID" ;;
    esac
  elif grep -q '^POLAR_ORG_ID = "[^"]' shotfleet.py; then warn "POLAR_ORG_ID not set; shotfleet.py keeps its current value"
  else fail "POLAR_ORG_ID not set and shotfleet.py has none: released builds could not check Polar keys"; fi
  if [ -n "$GUMROAD_URL" ] && [ -z "$GUMROAD_ID" ]; then fail "a Gumroad product URL needs the product ID too"; fi
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
    warn "not checked here (needs the network): xcrun notarytool history --keychain-profile ${NOTARY_PROFILE:-KeysiNotary}; (cd site && npx wrangler whoami)"
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
}

if [ -n "${POLAR_ORG_ID:-}" ]; then  # the released program checks Polar keys against this organization
  sed -i '' "s/^POLAR_ORG_ID = .*/POLAR_ORG_ID = \"$POLAR_ORG_ID\"  # set by packaging\/go-live.sh/" shotfleet.py
  git add shotfleet.py && git commit $GITOPTS -m "Polar organization ID for licence checks"
fi
if [ -n "$GUMROAD_URL" ]; then  # the released program checks Gumroad keys against this product
  : "${GUMROAD_ID:?a Gumroad product URL needs the product ID too (LAUNCH.md step 2)}"
  sed -i '' "s/^GUMROAD_PRODUCT_ID = .*/GUMROAD_PRODUCT_ID = \"$GUMROAD_ID\"  # set by packaging\/go-live.sh/" shotfleet.py
  git add shotfleet.py && git commit $GITOPTS -m "Gumroad product ID for licence checks"
fi
if [ "$DRY" = 0 ]; then packaging/release.sh; fi
transform_site
if [ "$DRY" = 0 ]; then
  (cd site && npx --yes wrangler@latest deploy)
  git add site/public/index.html && git commit -m "Site: sale open" && git push
  echo; echo "Live. Waitlist to email (marketing/launch-email.md):"; site/signups.sh
  exit 0
fi

# ---- dry run only from here: check the copy, show what changed, list what the real run does ----
git add site/public/index.html && git commit -q -m "Site: sale open"
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
grep -qF "first 100 buyers" "$H" && ok 'founder price text is static: "first 100 buyers" (no counter number)' || fail "the page lost its 'first 100 buyers' text"
if grep -Eiq '[0-9]+ (of 100|left|remaining)|spots? left' "$H"; then fail "page shows a counter number that nothing feeds"; else ok "no counter number on the page"; fi
[ "$(grep -cF 'curl -fsSL https://shotfleet.com/install.sh | sh' "$H")" = 1 ] && ok "install line appears once" || fail "install line count is not 1"
python3 -m py_compile shotfleet.py && ok "shotfleet.py compiles" || fail "shotfleet.py does not compile"
rm -rf __pycache__
if [ -n "${POLAR_ORG_ID:-}" ]; then grep -qF "POLAR_ORG_ID = \"$POLAR_ORG_ID\"" shotfleet.py && ok "POLAR_ORG_ID line set" || fail "POLAR_ORG_ID line not set"; fi
VERSION=$(python3 -c 'import re;print(re.search(r"VERSION = \"(.+?)\"", open("shotfleet.py").read()).group(1))')
if [ "${GOLIVE_SKIP_TESTS:-}" = 1 ]; then warn "claims check on the copy skipped (GOLIVE_SKIP_TESTS=1)"
else
  echo "-- claims check on the copy (the state the real run would deploy)"
  if SHOTFLEET_DRYRUN=1 tools/check-claims.sh >"$W/claims.log" 2>&1; then ok "$(tail -1 "$W/claims.log")"; else cat "$W/claims.log"; fail "claims check fails on the transformed copy"; fi
  rm -f "$W/claims.log"
fi
echo "-- the real run would, in this order"
say "1. sed POLAR_ORG_ID in shotfleet.py to ${POLAR_ORG_ID:-(unset: no edit)} and commit \"Polar organization ID for licence checks\""
if [ -n "$GUMROAD_URL" ]; then say "2. sed GUMROAD_PRODUCT_ID to $GUMROAD_ID and commit; the page keeps its Gumroad link $GUMROAD_URL"
else say "2. skip Gumroad (no URL given); the data-gumroad lines are dropped from the page"; fi
say "3. packaging/release.sh: tools/check-claims.sh, build $VERSION (sign with DEVELOPER_ID, notarize with ${NOTARY_PROFILE:-KeysiNotary}), copy to site/public/download, write VERSION, wrangler deploy (first deploy: still the waitlist page)"
say "4. transform site/public/index.html (drop WAITLIST blocks, open SALE blocks with $CHECKOUT, Early access -> Buy shotfleet)"
say "5. (cd site && npx wrangler deploy): the sale page goes live on shotfleet.com"
say "6. commit \"Site: sale open\" and git push (needs the upstream the check above found)"
say "7. site/signups.sh: print the waitlist emails for marketing/launch-email.md"
echo "after step 5, run: tools/golive/smoke.sh https://shotfleet.com $CHECKOUT"
[ -n "${GOLIVE_DRYRUN_DIR:-}" ] && echo "copy kept in $W"
if [ "$BAD" = 1 ]; then echo "== DRY RUN FOUND PROBLEMS: do not run the real go-live yet =="; exit 1; fi
echo "== dry run clean: nothing was built, deployed or pushed =="
