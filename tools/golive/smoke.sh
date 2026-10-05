#!/bin/sh
# Post-deploy smoke test of the live site (or of any server that serves a copy of it):
#   tools/golive/smoke.sh https://shotfleet.com [<checkout link the page must use>]
# Read-only: it fetches pages and the release, verifies them in a temp dir and installs nothing (install.sh is run
# only up to its checksum check, with a fake Apple silicon uname, and its HOME is the temp dir).
# Works from a clean environment: env -i sh tools/golive/smoke.sh https://shotfleet.com
PATH=/usr/bin:/bin:/usr/sbin:/sbin; export PATH
BASE=${1:?usage: tools/golive/smoke.sh <base url, e.g. https://shotfleet.com> [<checkout link>]}; BASE=${BASE%/}
CHECKOUT=${2:-}
ARCHIVE=shotfleet-macos-arm64.tar.gz  # the names install.sh asks for
T=$(mktemp -d) && trap 'rm -rf "$T"' EXIT
N=0; BAD=0
ok() { N=$((N + 1)); echo "  ok    $*"; }
skip() { echo "  SKIP  $*"; }
fail() { N=$((N + 1)); BAD=$((BAD + 1)); echo "  FAIL  $*"; }
sha256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi; }
# get <path> <name>: body in $T/<name>, headers in $T/<name>.h, status in $CODE (redirects are not followed)
get() { CODE=$(curl -sS --max-time 120 -o "$T/$2" -D "$T/$2.h" -w '%{http_code}' "$BASE$1" 2>"$T/err") || CODE=000; }
status200() { get "$1" "$2"; if [ "$CODE" = 200 ]; then ok "$1 is 200"; else fail "$1 is $CODE (want 200) $(cat "$T/err")"; return 1; fi; }

echo "== smoke: $BASE =="
if status200 / page; then
  P=$T/page
  for m in WAITLIST SALE @CHECKOUT@ @GUMROAD@ data-signup 'id="signup' "Join the list" "Early access" "isn’t released yet"; do
    if grep -qF -- "$m" "$P"; then fail "sale page still contains: $m"; else ok "sale page has no $m"; fi
  done
  if [ -n "$CHECKOUT" ]; then
    C=$(grep -cF "href=\"$CHECKOUT\"" "$P" || true)
    if [ "$C" -ge 3 ]; then ok "checkout link $CHECKOUT in $C places"; else fail "checkout link $CHECKOUT in $C places (want 3: nav, hero, price card)"; fi
  else
    C=$(grep -o 'href="https://[^"]*"' "$P" | grep -v 'href="https://shotfleet.com' | grep -c 'gumroad\|checkout' || true)
    if [ "$C" -ge 1 ]; then ok "page has a checkout link (pass the link as 2nd argument to check it exactly)"; else fail "no checkout link on the page"; fi
  fi
  if grep -qF "Buy shotfleet" "$P"; then ok "page says Buy shotfleet"; else fail "page does not say Buy shotfleet"; fi
  if grep -qF "first 100 buyers" "$P"; then ok 'founder price is the static text "first 100 buyers"'; else fail 'page lacks "first 100 buyers"'; fi
  if grep -Eiq '[0-9]+ (of 100|left|remaining)|spots? left' "$P"; then fail "page shows a counter number nothing feeds"; else ok "page shows no counter number"; fi
  CSP=$(grep -i '^content-security-policy:' "$T/page.h" || true)
  case "$CSP" in
    *"default-src 'self'"*"script-src 'self'"*) ok "CSP header present, scripts only from self" ;;
    *) fail "CSP header missing or weaker than site/public/_headers: ${CSP:-none}" ;;
  esac
fi

if status200 /install.sh inst; then
  if head -1 "$T/inst" | grep -q '^#!/bin/sh'; then ok "install.sh is a shell script"; else fail "install.sh is not a shell script (an HTML page?)"; fi
  if grep -qi '^content-type:.*text/html' "$T/inst.h"; then fail "install.sh is served as HTML"; fi
  if grep -q 'arm64' "$T/inst" && grep -q 'shasum -a 256' "$T/inst"; then ok "install.sh refuses non-arm64 and checks SHA-256"; else fail "install.sh lost its arm64 or checksum check"; fi
fi
VER=
if status200 /download/VERSION version; then
  VER=$(cat "$T/version")
  case "$VER" in [0-9]*.[0-9]*.[0-9]*) ok "VERSION is $VER" ;; *) fail "VERSION is not a version number: $VER" ;; esac
fi
if status200 "/download/$ARCHIVE" archive; then
  if [ -s "$T/archive" ]; then ok "archive is not empty ($(wc -c < "$T/archive" | tr -d ' ') bytes)"; else fail "archive is empty"; fi
fi
if status200 "/download/$ARCHIVE.sha256" sum; then
  SUM=$(cut -d' ' -f1 "$T/sum"); NAME=$(awk '{print $NF}' "$T/sum")
  case "$SUM" in
    *[!0-9a-f]*|"") fail ".sha256 does not start with a hex digest" ;;
    *) if [ ${#SUM} = 64 ]; then ok ".sha256 holds a SHA-256"; else fail ".sha256 digest has the wrong length"; fi ;;
  esac
  if [ "$NAME" = "$ARCHIVE" ]; then ok ".sha256 names $ARCHIVE"; else fail ".sha256 names '$NAME', not $ARCHIVE"; fi
  if [ -s "$T/archive" ]; then
    if [ "$(sha256 "$T/archive")" = "$SUM" ]; then ok "archive matches its .sha256"; else fail "archive does NOT match its .sha256"; fi
  fi
fi

# install.sh's own download and checksum lines, run unchanged, stopped before it extracts anything.
if [ -s "$T/inst" ] && grep -q '^tar -xzf' "$T/inst"; then
  mkdir -p "$T/shim" "$T/home"
  printf '#!/bin/sh\ncase "$1" in -s) echo Darwin;; -m) echo arm64;; *) exec /usr/bin/uname "$@";; esac\n' > "$T/shim/uname"; chmod +x "$T/shim/uname"
  sed '/^tar -xzf/,$d' "$T/inst" > "$T/inst-checksum.sh"; echo 'echo checksum-logic-ok' >> "$T/inst-checksum.sh"
  if OUT=$(env -i HOME="$T/home" PATH="$T/shim:$PATH" SHOTFLEET_BASE="$BASE/download" sh "$T/inst-checksum.sh" 2>&1) && [ "$OUT" = checksum-logic-ok ]; then
    ok "install.sh's checksum logic accepts the served archive"
  else fail "install.sh's checksum logic rejects the served archive: $OUT"; fi
else fail "install.sh has no 'tar -xzf' line to stop at: update tools/golive/smoke.sh"; fi

# The program itself, unpacked in the temp dir, reports the version the site announces.
if [ -s "$T/archive" ] && [ "$(uname -s)-$(uname -m)" = Darwin-arm64 ] && [ -n "$VER" ]; then
  mkdir "$T/x" && tar -xzf "$T/archive" -C "$T/x" 2>/dev/null
  GOT=$(env -i HOME="$T/home" PATH="$PATH" "$T/x/shotfleet/shotfleet" --version 2>&1 || true)
  if [ "$GOT" = "shotfleet $VER" ]; then ok "unpacked program says '$GOT'"; else fail "unpacked program says '${GOT:-nothing}', VERSION says $VER"; fi
else skip "running the program needs an Apple silicon Mac"; fi

if status200 /robots.txt robots; then
  if grep -qi '^sitemap:' "$T/robots"; then ok "robots.txt names the sitemap"; else fail "robots.txt has no Sitemap line"; fi
fi
if status200 /sitemap.xml sitemap; then
  if grep -q '<urlset' "$T/sitemap"; then ok "sitemap.xml is a sitemap"; else fail "sitemap.xml is not a sitemap"; fi
fi
for p in alternatives terms privacy; do status200 "/$p" "page-$p" || true; done

case "${SMOKE_SKIP_REDIRECT:+skip}$BASE" in
  skip*) skip "http to https redirect (SMOKE_SKIP_REDIRECT: workers.dev does not redirect)" ;;
  https://*)
    CODE=$(curl -sS --max-time 60 -o /dev/null -D "$T/redir.h" -w '%{http_code}' "http://${BASE#https://}/" 2>/dev/null) || CODE=000
    case "$CODE" in
      301|302|307|308) if grep -qi '^location: https://' "$T/redir.h"; then ok "http redirects to https ($CODE)"; else fail "http redirects ($CODE) but not to https"; fi ;;
      *) fail "http://${BASE#https://}/ answers $CODE, not a redirect to https" ;;
    esac ;;
  *) skip "http to https redirect (the base URL is not https)" ;;
esac

echo "smoke: $N checks, $BAD failed"
[ "$BAD" = 0 ]
