#!/bin/sh
# Prints the numbers STATUS.md quotes, read from the repo and the live site. Read only: no build, deploy, push or device.
#   tools/status.sh           everything (the tests take about 30 s)
#   tools/status.sh --quick   skip the tests
# Dependency-free: sh, python3, curl, git, node (only for the worker tests).
cd "$(dirname "$0")/.." || exit 1
SITE=${SHOTFLEET_SITE:-https://shotfleet.com}
QUICK=0; [ "${1:-}" = --quick ] && QUICK=1

echo "== when: $(date '+%Y-%m-%d %H:%M') on $(git rev-parse --abbrev-ref HEAD) at $(git rev-parse --short HEAD)"

echo "== tests"
if [ "$QUICK" = 1 ]; then echo "skipped (--quick)"; else
  out=$(mktemp); trap 'rm -f "$out"' EXIT
  python3 -m unittest discover -s tests >"$out" 2>&1; py=$?
  echo "python: $(grep -E '^(Ran |OK|FAILED)' "$out" | tr '\n' ' ')(exit $py)"
  node site/worker.test.mjs >"$out" 2>&1; js=$?
  echo "worker: $(grep -c '^ok' "$out") ok, $(grep -c '^FAIL' "$out") failed (exit $js)"
fi

echo "== claims register (tests/claims.json)"
python3 - <<'E'
import json, collections
c = json.load(open("tests/claims.json"))
n = collections.Counter(x["status"] for x in c)
print(f"{len(c)} claims: " + ", ".join(f"{k} {v}" for k, v in n.most_common()))
# strict reading used by STATUS.md: only 'proven' and 'fixed' are green; the rest still needs a run, a test or a human
green = n["proven"] + n["fixed"]
print(f"green (proven+fixed) {green}, needs work (everything else except removed) {len(c) - green - n['removed']}")
E

echo "== release state in the repo"
for k in POLAR_ORG_ID GUMROAD_PRODUCT_ID; do
  v=$(sed -n "s/^$k = \"\\([^\"]*\\)\".*/\\1/p" shotfleet.py | head -1)
  echo "$k in shotfleet.py: ${v:+set}${v:-EMPTY (go-live.sh sets it)}"
done
echo "version in shotfleet.py: $(sed -n 's/^VERSION = "\(.*\)"/\1/p' shotfleet.py)"
if grep -q 'WAITLIST' site/public/index.html; then echo "site/public/index.html: waitlist mode (sale not switched on)"; else echo "site/public/index.html: sale mode"; fi
[ -d site/public/download ] && echo "site/public/download: present" || echo "site/public/download: absent (no release copied yet)"

echo "== live site ($SITE)"
for p in / /install.sh /download/VERSION /download/shotfleet-macos-arm64.tar.gz /robots.txt /sitemap.xml /alternatives /docs /privacy /terms /llms.txt /ga.js; do
  printf '%-40s %s\n' "$p" "$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$SITE$p")"
done
printf '%-40s %s\n' "http -> https" "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 15 "http://${SITE#https://}/")"
printf '%-40s %s\n' "www -> apex" "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 15 "https://www.${SITE#https://}/")"
printf '%-40s %s\n' "CSP header" "$(curl -sI --max-time 15 "$SITE/" | grep -ic '^content-security-policy')"
live=$(mktemp); curl -s --max-time 15 "$SITE/" -o "$live"
if cmp -s "$live" site/public/index.html; then echo "live index.html == repo"; else echo "live index.html DIFFERS from repo (undeployed changes, or the page is in flux)"; fi
echo "live page mentions: waitlist $(grep -ci waitlist "$live"), polar $(grep -ci polar "$live"), gumroad $(grep -ci gumroad "$live"), buy link $(grep -c 'buy.polar.sh\|gumroad.com/l/' "$live")"
rm -f "$live"

echo "== git"
echo "commits: $(git rev-list --count HEAD) total, $(git rev-list --count --since='7 days ago' HEAD) in the last 7 days"
git log -10 --format='%h %ad %s' --date=format:'%m-%d %H:%M' | cut -c1-110
st=$(git status --short); [ -n "$st" ] && { echo "uncommitted (other work in flux):"; echo "$st"; } || echo "working tree clean"

echo "== this Mac"
df -h /System/Volumes/Data 2>/dev/null | tail -1 | awk '{print "disk (Data volume): " $4 " free, " $5 " used"}'
