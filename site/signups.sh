#!/bin/sh
# Waitlist signups and contact messages stored by worker.js.
#   ./signups.sh            count + email addresses, then messages
#   ./signups.sh --details  also each signup's platform / country / source
#   ./signups.sh --purge-waitlist   delete every email: record (do this 30 days after the launch email; messages and visit counts stay)
cd "$(dirname "$0")"
if [ "${1:-}" = "--purge-waitlist" ]; then
  names=$(npx -y wrangler@latest kv key list --binding WAITLIST --remote --prefix email: 2>/dev/null \
    | python3 -c "import json,sys; print(json.dumps([k['name'] for k in json.load(sys.stdin)]))") || { echo "could not list the waitlist" >&2; exit 1; }
  echo "$names" | python3 -c "import json,sys; print(len(json.load(sys.stdin)), 'waitlist emails will be deleted (messages and visit counts stay)')"
  printf 'Type PURGE to delete them: '; read -r answer
  [ "$answer" = PURGE ] || { echo "nothing deleted"; exit 1; }
  file=$(mktemp); echo "$names" > "$file"   # ponytail: one list page (1,000 keys); run it again if more are left
  npx -y wrangler@latest kv bulk delete "$file" --binding WAITLIST --remote --force && rm -f "$file" && echo "deleted"
  exit
fi
keys=$(npx -y wrangler@latest kv key list --binding WAITLIST --remote 2>/dev/null)
echo "$keys" | python3 -c "
import json,sys; names=[k['name'] for k in json.load(sys.stdin)]
emails=[n[6:] for n in names if n.startswith('email:')]
print(len(emails), 'signups'); print('\n'.join(emails))
msgs=[n for n in names if n.startswith('msg:')]
print(); print(len(msgs), 'messages'); print('\n'.join(msgs))" > /tmp/shotfleet_keys.txt
cat /tmp/shotfleet_keys.txt
if [ "${1:-}" = "--details" ] || grep -q "^msg:" /tmp/shotfleet_keys.txt; then
  for k in $(echo "$keys" | python3 -c "import json,sys;print(' '.join(k['name'] for k in json.load(sys.stdin) if k['name'].startswith('msg:') or '${1:-}'=='--details'))"); do
    printf '\n%s\n  ' "$k"; npx -y wrangler@latest kv key get "$k" --binding WAITLIST --remote 2>/dev/null
  done; echo
fi
# ./signups.sh --visits    page events by day / source / browser language / event (totals only)
if [ "${1:-}" = "--visits" ]; then
  for k in $(npx -y wrangler@latest kv key list --binding WAITLIST --remote --prefix hit: 2>/dev/null | python3 -c "import json,sys;print(' '.join(k['name'].replace('|','%7C') for k in json.load(sys.stdin)))"); do
    k=$(printf '%s' "$k" | sed 's/%7C/|/g'); printf '%s  ' "$k"; npx -y wrangler@latest kv key get "$k" --binding WAITLIST --remote 2>/dev/null; echo
  done
fi
