#!/bin/sh
# Read-only checks to run before any release (build, publish): nothing is built, signed, uploaded or changed, and no secret is printed.
#   packaging/preflight.sh
# Checks: the Developer ID Application and Installer certificates are in the keychain and not close to expiry, notarytool reaches Apple with the
# keychain profile (network), wrangler is logged in (network), the git tree is clean, enough disk is free, the uv-managed standalone Python 3.14
# exists and needs macOS 11.0 (a Homebrew Python would make the build need the build Mac's macOS).
# Each check prints OK or FAIL with the reason; exit 1 when any check fails.
# Variables: DEVELOPER_ID, INSTALLER_ID, NOTARY_PROFILE (defaults as in packaging/release.sh), MIN_FREE_GB (5), MIN_CERT_DAYS (14),
# WRANGLER ("npx --yes wrangler@latest"), PYTHON_MINOS_MAX (11).
PATH=/usr/bin:/bin:/usr/sbin:/sbin:$PATH; export PATH
case "${1:-}" in -h|--help) sed -n '2,/^PATH=/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; exit 0 ;; "") ;; *) echo "unknown argument: $1 (see --help)" >&2; exit 2 ;; esac
cd "$(dirname "$0")/.." || exit 2
DEVELOPER_ID=${DEVELOPER_ID:-Developer ID Application: Manuel Lorenzo Parejo (2357A78TMR)}
INSTALLER_ID=${INSTALLER_ID:-Developer ID Installer: Manuel Lorenzo Parejo (2357A78TMR)}
NOTARY_PROFILE=${NOTARY_PROFILE:-KeysiNotary}
MIN_FREE_GB=${MIN_FREE_GB:-5}; MIN_CERT_DAYS=${MIN_CERT_DAYS:-14}; WRANGLER=${WRANGLER:-npx --yes wrangler@latest}; MINOS_MAX=${PYTHON_MINOS_MAX:-11}
T=$(mktemp -d) && trap 'rm -rf "$T"' EXIT
BAD=0
ok() { echo "OK    $*"; }
fail() { BAD=$((BAD + 1)); echo "FAIL  $*"; }
timed() { perl -e 'alarm shift; exec @ARGV' "$@"; }  # <seconds> <command...>: a hung network call must not hang the preflight

idents=$(security find-identity -v 2>/dev/null)
for kind in "Developer ID Application:$DEVELOPER_ID" "Developer ID Installer:$INSTALLER_ID"; do
  label=${kind%%:*}; id=${kind#*:}
  if ! echo "$idents" | grep -qF "\"$id\""; then fail "$label certificate with its private key is not in the keychain: $id"; continue; fi
  if ! security find-certificate -c "$id" -p 2>/dev/null > "$T/cert.pem" || [ ! -s "$T/cert.pem" ]; then fail "$label: cannot read the certificate for $id"; continue; fi
  end=$(openssl x509 -noout -enddate < "$T/cert.pem" 2>/dev/null | sed 's/notAfter=//')
  if ! openssl x509 -noout -checkend 0 < "$T/cert.pem" >/dev/null 2>&1; then fail "$label certificate EXPIRED ($end): $id"
  elif ! openssl x509 -noout -checkend $((MIN_CERT_DAYS * 86400)) < "$T/cert.pem" >/dev/null 2>&1; then fail "$label certificate expires within $MIN_CERT_DAYS days ($end): $id"
  else ok "$label certificate present, valid until $end"; fi
done

if timed 60 xcrun notarytool history --keychain-profile "$NOTARY_PROFILE" >"$T/nt.out" 2>&1; then ok "notarytool history works with the keychain profile $NOTARY_PROFILE"
else fail "notarytool history failed with the keychain profile $NOTARY_PROFILE (not stored, no network, or Apple is down): $(grep -iv 'password\|token' "$T/nt.out" | head -1 | cut -c1-100)"; fi

# shellcheck disable=SC2086  # $WRANGLER is a command with arguments
if [ -d site ] && (cd site && timed 90 $WRANGLER whoami >"$T/who.out" 2>&1) && grep -qi 'logged in' "$T/who.out"; then ok "wrangler is logged in to Cloudflare"
else fail "wrangler whoami: not logged in or unreachable (run: cd site && npx wrangler login)"; fi

if [ -z "$(git status --porcelain 2>/dev/null)" ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ok "git tree is clean ($(git rev-parse --short HEAD))"
else fail "git tree is not clean (or this is not a git work tree): the build would include uncommitted changes"; fi

free_kb=$(df -k . | awk 'NR == 2 { print $4 }')
if [ "${free_kb:-0}" -ge $((MIN_FREE_GB * 1024 * 1024)) ]; then ok "free disk $((free_kb / 1024 / 1024)) GB (need $MIN_FREE_GB)"; else fail "free disk $((${free_kb:-0} / 1024 / 1024)) GB, need $MIN_FREE_GB"; fi

PY=$(uv python find 3.14 --managed-python 2>/dev/null)
if [ -z "$PY" ] || [ ! -x "$PY" ]; then fail "no uv-managed standalone Python 3.14 (run: uv python install 3.14); Homebrew's Python would make the build need this Mac's macOS"
else
  mkdir "$T/py" && cp "$(python3 -c 'import os,sys;print(os.path.realpath(sys.argv[1]))' "$PY")" "$T/py/python"  # macho-minos reads regular files only
  if python3 tools/macho-minos.py "$T/py" --max "$MINOS_MAX" >"$T/minos.out" 2>&1; then ok "managed Python $("$PY" -c 'import sys;print(sys.version.split()[0])') at $PY needs macOS $(grep -o 'macOS [0-9.]* or newer' "$T/minos.out" | awk '{print $2}') (maximum $MINOS_MAX.0)"
  else fail "managed Python at $PY needs a newer macOS than $MINOS_MAX.0: $(tail -2 "$T/minos.out" | head -1 | tr -s ' ')"; fi
fi

if [ "$BAD" = 0 ]; then echo "preflight: all checks OK"; exit 0; fi
echo "preflight: $BAD check(s) FAILED"; exit 1
