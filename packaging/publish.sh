#!/bin/sh
# Publish ALREADY TESTED release files on the shotfleet site. It builds nothing: build with packaging/build.sh, test and gate those
# exact files, record their hashes, then publish them. The full flow is in packaging/README.md.
#
#   packaging/publish.sh --make-manifest <version> <tarball> <pkg>      > manifest.txt   (record what was tested)
#   SHOTFLEET_RELEASE_DIR=<durable dir> packaging/publish.sh [--dry-run] --manifest manifest.txt --artifacts <dir> [--checkout <url>] [--tree <dir>]
#
# --dry-run runs every check (manifest hashes, versions, tree, the live version id read) and prints the plan; it stages, archives, deploys
# and rolls back nothing and writes nothing but its own output.
#
# The real run: checks -> stage the files into <tree>/site/public/download -> archive the shipped bytes -> record the live Cloudflare version id
# in a durable file -> wrangler deploy -> verify the served files, VERSION, install.sh, smoke.sh and a live install into a temp HOME ->
# roll back to the recorded id on ANY failure (also on Ctrl-C, or when this script dies).
#
# Variables: SHOTFLEET_RELEASE_DIR (required, not under /tmp: gets state/ and archive/), PUBLISH_BASE (https://shotfleet.com),
# WRANGLER ("npx --yes wrangler@latest"), PUBLISH_SMOKE (command run as: env -i $PUBLISH_SMOKE <base> [<checkout>]; default tools/golive/smoke.sh),
# PUBLISH_ALLOW_BRANCH=1 (publish a tree whose HEAD is not origin/main), SHOTFLEET_ALLOW_TMP_DIR=1 (honoured only with --dry-run).
set -eu
PATH=$PATH:/usr/bin:/bin; export PATH

sha256() { if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d' ' -f1; else sha256sum "$1" | cut -d' ' -f1; fi; }
size() { wc -c < "$1" | tr -d ' '; }
usage() { sed -n '2,/^set -eu/p' "$0" | sed '$d' | sed 's/^# \{0,1\}//'; }

if [ "${1:-}" = --make-manifest ]; then
  [ $# = 4 ] || { echo "usage: packaging/publish.sh --make-manifest <version> <tarball> <pkg>" >&2; exit 2; }
  V=$2; shift 2
  echo "# shotfleet release manifest: the files that were tested; packaging/publish.sh refuses anything else"
  echo "version $V"
  for f in "$@"; do [ -f "$f" ] || { echo "no such file: $f" >&2; exit 2; }; echo "file $(sha256 "$f") $(size "$f") $(basename "$f")"; done
  exit 0
fi

DRY=0; MANIFEST=; ARTIFACTS=; CHECKOUT=; TREE=
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1 ;;
    --manifest) MANIFEST=${2:?--manifest needs a file}; shift ;;
    --artifacts) ARTIFACTS=${2:?--artifacts needs a folder}; shift ;;
    --checkout) CHECKOUT=${2:?--checkout needs a URL}; shift ;;
    --tree) TREE=${2:?--tree needs a folder}; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown argument: $1 (see --help)" >&2; exit 2 ;;
  esac
  shift
done
[ -n "$MANIFEST" ] && [ -n "$ARTIFACTS" ] || { echo "usage: packaging/publish.sh [--dry-run] --manifest <file> --artifacts <dir> (see --help)" >&2; exit 2; }
[ -f "$MANIFEST" ] || { echo "no such manifest: $MANIFEST" >&2; exit 2; }
[ -d "$ARTIFACTS" ] || { echo "no such artifacts folder: $ARTIFACTS" >&2; exit 2; }
ARTIFACTS=$(cd "$ARTIFACTS" && pwd); MANIFEST=$(cd "$(dirname "$MANIFEST")" && pwd)/$(basename "$MANIFEST")
[ -n "$TREE" ] || TREE=$(cd "$(dirname "$0")/.." && pwd)
[ -d "$TREE" ] || { echo "no such tree: $TREE" >&2; exit 2; }
TREE=$(cd "$TREE" && pwd)
BASE=${PUBLISH_BASE:-https://shotfleet.com}; BASE=${BASE%/}
WRANGLER=${WRANGLER:-npx --yes wrangler@latest}
SMOKE=${PUBLISH_SMOKE:-sh $TREE/tools/golive/smoke.sh}
BAD=0
ok() { echo "  ok    $*"; }
warn() { echo "  WARN  $*"; }
fail() { BAD=$((BAD + 1)); echo "  FAIL  $*"; }
log() { echo "$(date +%H:%M:%S) $*"; }

echo "== publish $( [ "$DRY" = 1 ] && echo 'DRY RUN: deploys, rolls back and writes nothing' || echo 'REAL RUN') =="
echo "-- manifest and files"
VERSION=$(awk '$1 == "version" { print $2 }' "$MANIFEST")
case "$VERSION" in [0-9]*.[0-9]*.[0-9]*) ok "manifest version $VERSION" ;; *) fail "manifest has no 'version X.Y.Z' line"; VERSION=unknown ;; esac
TAR=shotfleet-$VERSION-macos-arm64.tar.gz; PKG=shotfleet-$VERSION-macos-arm64.pkg
[ "$(grep -c '^file ' "$MANIFEST")" = 2 ] || fail "the manifest must list exactly two files: $TAR and $PKG"
for n in "$TAR" "$PKG"; do
  line=$(awk -v n="$n" '$1 == "file" && $4 == n { print $2, $3 }' "$MANIFEST")
  if [ -z "$line" ]; then fail "manifest does not list $n"; continue; fi
  want_sha=${line% *}; want_size=${line#* }
  if [ ! -f "$ARTIFACTS/$n" ]; then fail "missing in $ARTIFACTS: $n"; continue; fi
  if [ "$(size "$ARTIFACTS/$n")" != "$want_size" ]; then fail "$n has $(size "$ARTIFACTS/$n") bytes, the manifest says $want_size"; continue; fi
  if [ "$(sha256 "$ARTIFACTS/$n")" != "$want_sha" ]; then fail "$n does not match its manifest sha256 (not the tested file)"; continue; fi
  ok "$n: $want_size bytes, sha256 ${want_sha%"${want_sha#????????????}"}..."
  case "$n" in *.tar.gz) TAR_SHA=$want_sha ;; *) PKG_SHA=$want_sha ;; esac
done

echo "-- tree $TREE"
for f in shotfleet.py CHANGELOG.md site/public/docs.html site/public/install.sh site/wrangler.toml tools/golive/smoke.sh; do
  [ -f "$TREE/$f" ] || fail "tree lacks $f"
done
V_PY=$(sed -n 's/^VERSION = "\(.*\)".*/\1/p' "$TREE/shotfleet.py" 2>/dev/null | head -1)
V_CL=$(grep -m1 -E '^## [0-9]+\.[0-9]+\.[0-9]+' "$TREE/CHANGELOG.md" 2>/dev/null | awk '{ print $2 }')
V_DOC=$(sed -n 's/.*Last checked against version \([0-9][0-9.]*\) on.*/\1/p' "$TREE/site/public/docs.html" 2>/dev/null | head -1)
if [ "$V_PY" = "$VERSION" ] && [ "$V_CL" = "$VERSION" ] && [ "$V_DOC" = "$VERSION" ]; then ok "VERSION agrees: manifest, shotfleet.py, top CHANGELOG heading and docs 'Last checked' line all say $VERSION"
else fail "VERSION disagrees: manifest '$VERSION', shotfleet.py '$V_PY', top CHANGELOG heading '$V_CL', docs page '$V_DOC'"; fi
[ ! -e "$TREE/RESUME.md" ] || fail "RESUME.md is in the tree (the coordinator deletes it before merge)"
if git -C "$TREE" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$TREE" fetch -q origin 2>/dev/null || warn "git fetch failed: origin/main may be stale"
  if [ -n "$(git -C "$TREE" status --porcelain)" ]; then fail "the git tree is not clean (the deploy would ship uncommitted site files)"; else ok "git tree is clean"; fi
  if git -C "$TREE" rev-parse -q --verify origin/main >/dev/null && [ "$(git -C "$TREE" rev-parse HEAD)" = "$(git -C "$TREE" rev-parse origin/main)" ]; then ok "HEAD is origin/main ($(git -C "$TREE" rev-parse --short HEAD))"
  elif [ "${PUBLISH_ALLOW_BRANCH:-}" = 1 ]; then warn "HEAD is not origin/main (PUBLISH_ALLOW_BRANCH=1)"
  else fail "HEAD is not origin/main: deploy from a fresh worktree of main (or set PUBLISH_ALLOW_BRANCH=1)"; fi
else fail "$TREE is not a git work tree"; fi

echo "-- durable directory"
REL=${SHOTFLEET_RELEASE_DIR:-}
case "$REL" in
  "") fail "SHOTFLEET_RELEASE_DIR is not set: it names where the rollback id and the shipped bytes are kept" ;;
  /*) STATE=$REL/state; ARCH=$REL/archive/$VERSION
      case "$REL" in
        /tmp|/tmp/*|/private/tmp|/private/tmp/*|/var/tmp/*|/private/var/tmp/*|/var/folders/*|/private/var/folders/*)
          if [ "$DRY" = 1 ] && [ "${SHOTFLEET_ALLOW_TMP_DIR:-}" = 1 ]; then warn "$REL is a temporary directory (allowed for a dry run)"
          else fail "SHOTFLEET_RELEASE_DIR is under a temporary directory ($REL): /tmp is wiped; use a durable folder"; fi ;;
        *) ok "release directory $REL" ;;
      esac ;;
  *) fail "SHOTFLEET_RELEASE_DIR must be an absolute path: $REL" ;;
esac

echo "-- live site (read-only)"
live_id() { (cd "$TREE/site" && $WRANGLER deployments list 2>/dev/null) | grep -o 'Version(s):  *([0-9]*%) [0-9a-f-]*' | tail -1 | awk '{ print $3 }' || true; }
OLDID=$(live_id)
case "$OLDID" in
  ????????-????-????-????-????????????) ok "live Cloudflare version id (the rollback target): $OLDID" ;;
  *) if [ "$DRY" = 1 ]; then warn "could not read the live version id (wrangler deployments list); the real run would refuse"; else fail "could not read the live Cloudflare version id: refusing to deploy without a rollback target"; fi ;;
esac
LIVE_VERSION=$(curl -s --max-time 20 "$BASE/download/VERSION" 2>/dev/null | head -c 20 || true)
echo "  live $BASE/download/VERSION says: ${LIVE_VERSION:-nothing}"

if [ "$BAD" != 0 ]; then echo "== REFUSED: $BAD check(s) failed; nothing was staged, archived or deployed =="; exit 1; fi

STAMP=$(date +%Y%m%d-%H%M%S)
D=$TREE/site/public/download
if [ "$DRY" = 1 ]; then
  echo "-- plan (nothing below was done)"
  echo "  would: rm -rf $D; copy $TAR -> $D/shotfleet-macos-arm64.tar.gz, $PKG -> $D/shotfleet-macos-arm64.pkg, write the .sha256 and VERSION ($VERSION)"
  echo "  would: archive the staged bytes plus SHA256SUMS in $ARCH (and the files now live, in $REL/archive/live-before-$VERSION)"
  echo "  would: write the rollback id $OLDID to $STATE/rollback-$VERSION-$STAMP.txt"
  echo "  would: (cd $TREE/site && $WRANGLER deploy)"
  echo "  would: verify $BASE: /download/VERSION = $VERSION, tarball, .sha256 and pkg hashes, install.sh 200, env -i $SMOKE $BASE ${CHECKOUT}, a live install into a temp HOME"
  echo "  would, on any failure: (cd $TREE/site && $WRANGLER rollback $OLDID -y)"
  echo "== dry run clean: every check passed; nothing was deployed =="
  exit 0
fi

# ---- real run ----
mkdir -p "$STATE" "$REL/archive"
T=$(mktemp -d); DEPLOYED=0; VERIFIED=0; NEWID=
rollback() {
  [ -n "$OLDID" ] || { log "NO ROLLBACK TARGET"; return; }
  cur=$(live_id)
  if [ "$cur" = "$OLDID" ]; then log "live is already the recorded version $OLDID: nothing to roll back"; return; fi
  log "ROLLING BACK to $OLDID"
  if (cd "$TREE/site" && $WRANGLER rollback "$OLDID" --message "rollback $VERSION: ${REASON:-script stopped}" -y); then log "rolled back to $OLDID; live VERSION now: $(curl -s --max-time 20 "$BASE/download/VERSION" || echo unknown)"
  else log "ROLLBACK COMMAND FAILED: roll back by hand: (cd site && $WRANGLER rollback $OLDID)"; fi
}
on_exit() { rc=$?; rm -rf "$T"; if [ "$DEPLOYED" = 1 ] && [ "$VERIFIED" != 1 ]; then rollback; [ "$rc" != 0 ] || rc=1; fi; exit "$rc"; }
trap on_exit EXIT; trap 'exit 130' INT TERM HUP
REASON=
bad() { REASON=$1; log "FAILED: $1"; exit 1; }

log "stage the tested files in $D"
rm -rf "$D"; mkdir -p "$D"
cp "$ARTIFACTS/$TAR" "$D/shotfleet-macos-arm64.tar.gz"; cp "$ARTIFACTS/$PKG" "$D/shotfleet-macos-arm64.pkg"
echo "$TAR_SHA  shotfleet-macos-arm64.tar.gz" > "$D/shotfleet-macos-arm64.tar.gz.sha256"; echo "$VERSION" > "$D/VERSION"
[ -d "$D" ] || bad "site/public/download is missing"
[ "$(sha256 "$D/shotfleet-macos-arm64.tar.gz")" = "$TAR_SHA" ] && [ "$(sha256 "$D/shotfleet-macos-arm64.pkg")" = "$PKG_SHA" ] || bad "staged files differ from the manifest"
[ "$(cat "$D/VERSION")" = "$VERSION" ] || bad "staged VERSION differs"

log "archive the shipped bytes in $ARCH"
(cd "$D" && shasum -a 256 shotfleet-macos-arm64.tar.gz shotfleet-macos-arm64.pkg > "$T/SHA256SUMS")
if [ -d "$ARCH" ]; then cmp -s "$T/SHA256SUMS" "$ARCH/SHA256SUMS" || bad "$ARCH exists with different files: move it aside"
else mkdir -p "$ARCH" && cp "$D"/* "$ARCH/" && cp "$T/SHA256SUMS" "$MANIFEST" "$ARCH/"; fi
# what is live now, for the record (0.1.0's live bytes were never kept); best effort
L=$REL/archive/live-before-$VERSION; mkdir -p "$L"
for n in shotfleet-macos-arm64.tar.gz shotfleet-macos-arm64.pkg shotfleet-macos-arm64.tar.gz.sha256 VERSION; do curl -fsS --max-time 180 -o "$L/$n" "$BASE/download/$n" 2>/dev/null || rm -f "$L/$n"; done

echo "$OLDID" > "$STATE/rollback-$VERSION-$STAMP.txt"; echo "version $VERSION; live before: ${LIVE_VERSION:-unknown}; recorded $STAMP" >> "$STATE/rollback-$VERSION-$STAMP.txt"
log "ROLLBACK TARGET $OLDID recorded in $STATE/rollback-$VERSION-$STAMP.txt"

log "wrangler deploy"
DEPLOYED=1
OUT=$(cd "$TREE/site" && $WRANGLER deploy 2>&1) || { echo "$OUT" | tail -5; bad "wrangler deploy failed"; }
NEWID=$(echo "$OUT" | grep -o 'Current Version ID: [0-9a-f-]*' | awk '{ print $4 }' || true)
log "deployed; new version id: ${NEWID:-not printed}"

log "verify the live site"
V=; sleep "${PUBLISH_SETTLE:-20}"
for i in 1 2 3 4 5 6; do V=$(curl -s --max-time 20 "$BASE/download/VERSION" || true); [ "$V" = "$VERSION" ] && break; sleep "${PUBLISH_RETRY:-15}"; done
[ "$V" = "$VERSION" ] || bad "VERSION says '$V', not $VERSION"
curl -fsS --max-time 180 -o "$T/a.tgz" "$BASE/download/shotfleet-macos-arm64.tar.gz" || bad "tarball not served"
curl -fsS --max-time 30 -o "$T/a.sha" "$BASE/download/shotfleet-macos-arm64.tar.gz.sha256" || bad ".sha256 not served"
curl -fsS --max-time 180 -o "$T/a.pkg" "$BASE/download/shotfleet-macos-arm64.pkg" || bad "pkg not served"
[ "$(sha256 "$T/a.tgz")" = "$TAR_SHA" ] || bad "served tarball hash differs"
[ "$(cut -c1-64 "$T/a.sha")" = "$TAR_SHA" ] || bad "served .sha256 differs"
[ "$(sha256 "$T/a.pkg")" = "$PKG_SHA" ] || bad "served pkg hash differs"
[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$BASE/install.sh")" = 200 ] || bad "install.sh is not 200"
log "served files verified: VERSION $VERSION, tarball $TAR_SHA, pkg $PKG_SHA, install.sh 200"
# shellcheck disable=SC2086  # $SMOKE is a command with arguments
env -i $SMOKE "$BASE" ${CHECKOUT:+"$CHECKOUT"} > "$T/smoke.out" 2>&1 || { tail -5 "$T/smoke.out"; bad "smoke test failed"; }
log "smoke passed: $(tail -1 "$T/smoke.out")"
if [ "$(uname -s)-$(uname -m)" = Darwin-arm64 ]; then
  mkdir -p "$T/home"; curl -s --max-time 30 "$BASE/install.sh" | sed 's|^for DIR in .*; do|for DIR in "$HOME/.local/bin"; do|' > "$T/home/install.sh"
  (cd "$T/home" && env -i HOME="$T/home" PATH=/usr/bin:/bin:/usr/sbin:/sbin SHOTFLEET_BASE="$BASE/download" sh install.sh) > "$T/install.out" 2>&1 || { tail -5 "$T/install.out"; bad "live install failed"; }
  GOT=$(env -i HOME="$T/home" PATH=/usr/bin:/bin:/usr/sbin:/sbin "$T/home/.local/bin/shotfleet" --version 2>&1 || true)
  [ "$GOT" = "shotfleet $VERSION" ] || bad "live install runs as '$GOT'"
  log "live install in a temp HOME: $GOT"
else warn "live install skipped: needs an Apple silicon Mac"; fi

VERIFIED=1
echo "version $VERSION; old id $OLDID; new id ${NEWID:-unknown}; tarball $TAR_SHA; pkg $PKG_SHA; verified $(date +%Y-%m-%dT%H:%M:%S)" > "$STATE/published-$VERSION-$STAMP.txt"
log "PUBLISHED $VERSION. Old version id $OLDID (rollback: cd site && $WRANGLER rollback $OLDID). Archive: $ARCH"
