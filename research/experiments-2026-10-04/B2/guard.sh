#!/bin/zsh
# usage: guard.sh <seconds> <script> [args...]  Hard time limit; on timeout kills the script by exact pid and cleans up ONLY my own devices.
LIMIT=$1; shift
"$@" &
P=$!; t=0
while kill -0 $P 2>/dev/null; do sleep 5; t=$((t+5)); if [ $t -ge $LIMIT ]; then echo "GUARD: limit $LIMIT s, killing exact pid $P"; pkill -TERM -P $P; kill $P; sleep 3; for e in emulator-5760 emulator-5762; do adb -s $e emu kill >/dev/null 2>&1; done; for u in $(xcrun simctl list devices 2>/dev/null | grep -E "expB2-ios18" | grep -oE '[0-9A-F]{8}-[0-9A-F-]{27}'); do xcrun simctl shutdown $u 2>/dev/null; xcrun simctl delete $u; done; echo "GUARD: cleaned own devices"; exit 124; fi; done
wait $P; echo "guard: script exit $?"
