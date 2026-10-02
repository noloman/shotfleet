#!/bin/sh
# Waitlist signups and contact messages stored by worker.js.
#   ./signups.sh            count + email addresses, then messages
#   ./signups.sh --details  also each signup's platform / country / source
cd "$(dirname "$0")"
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
# ./signups.sh --visits    page views by day / source / browser language (totals only)
if [ "${1:-}" = "--visits" ]; then
  for k in $(npx -y wrangler@latest kv key list --binding WAITLIST --remote --prefix hit: 2>/dev/null | python3 -c "import json,sys;print(' '.join(k['name'].replace('|','%7C') for k in json.load(sys.stdin)))"); do
    k=$(printf '%s' "$k" | sed 's/%7C/|/g'); printf '%s  ' "$k"; npx -y wrangler@latest kv key get "$k" --binding WAITLIST --remote 2>/dev/null; echo
  done
fi
