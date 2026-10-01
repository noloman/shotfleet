#!/bin/sh
# Waitlist signups stored by worker.js (count, then email / date / platform / country)
cd "$(dirname "$0")"
npx -y wrangler@latest kv key list --binding WAITLIST --remote 2>/dev/null \
  | python3 -c "import json,sys; keys=[k['name'][6:] for k in json.load(sys.stdin)]; print(len(keys), 'signups'); print('\n'.join(keys))"
