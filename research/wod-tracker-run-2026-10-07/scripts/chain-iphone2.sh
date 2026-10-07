#!/bin/bash
# WOD Tracker showcase, iPhone device job. Waits for the queue/lock/quiet rule, runs dry run + 3 pair runs, always cleans up.
S=/Users/manu/Developer/shotfleet-rc-build/showcase-wod
SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
Q=/tmp/shotfleet-device-queue.md; L=/tmp/shotfleet-devices.lock
MYLINE='- 2026-10-07 18:06 WOD Tracker showcase iPhone'
cd $S
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $S/progress.log; }
snap() { echo "load=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print $1}') free%=$(memory_pressure | awk -F': ' '/free percentage/ {print $2}') disk_free_GiB=$(/bin/df -g /Users/manu | awk 'NR==2{print $4}')"; }
HAVE_LOCK=0; RUNPG=""
cleanup() {
  trap - EXIT INT TERM
  log "CLEANUP start"
  if [ -n "$RUNPG" ] && kill -0 $RUNPG 2>/dev/null; then log "killing my own run group $RUNPG"; kill -TERM -$RUNPG 2>/dev/null; sleep 5; kill -KILL -$RUNPG 2>/dev/null; fi
  if [ $HAVE_LOCK = 1 ]; then
    # simulators: only what became booted/new during my hold; the pre-existing shotfleet-* pool names are shut down (I booted them) but never deleted
    xcrun simctl list devices > $S/logs/sims.after.txt 2>&1
    for u in $(grep -oE '[0-9A-F]{8}-[0-9A-F-]{27}' $S/logs/sims.after.txt | sort -u); do
      line=$(grep "$u" $S/logs/sims.after.txt)
      case "$line" in *shotfleet-*) ;; *) continue;; esac
      if grep -q "$u" $S/logs/sims.before.txt; then
        # existed before: shut it down only if it was NOT booted when I took the lock
        if ! grep "$u" $S/logs/sims.before.txt | grep -q Booted && echo "$line" | grep -q Booted; then xcrun simctl shutdown $u 2>/dev/null; log "shut down $u (pool sim, existed before, was shut down at lock time)"; fi
      else
        xcrun simctl shutdown $u 2>/dev/null; xcrun simctl delete $u 2>/dev/null; log "shut down + deleted NEW simulator $u"
      fi
    done
    xcrun simctl list devices > $S/logs/sims.final.txt 2>&1
    rm -rf $L; log "LOCK RELEASED ($(snap))"
    python3 - <<PY
import re
p="$Q"; t=open(p).read().split("\n")
t=[l for l in t if not l.startswith("$MYLINE")]
while t and t[-1]=="": t.pop()
t.append("- $(date '+%Y-%m-%d %H:%M') WOD Tracker showcase iPhone (OCR session): DONE, lock RELEASED, my simulators shut down")
open(p,"w").write("\n".join(t)+"\n")
PY
    log "queue line replaced by DONE line"
  fi
  echo finished > $S/chain-iphone.status
  log "CLEANUP end"
}
trap cleanup EXIT INT TERM
echo running > $S/chain-iphone.status
HAVE_LOCK=1; T0=$(date -j -f '%Y-%m-%d %H:%M:%S' '2026-10-07 18:14:38' +%s)
grep -q "WOD Tracker showcase iPhone (OCR session)" $L/holder || { log "lock is not mine, stopping"; HAVE_LOCK=0; exit 9; }
log "chain2 started pid $$: adopting my lock (taken 18:14:38), sims.before kept from the first chain"
DEADLINE=$(( T0 + 75*60 ))

runone() { # name locales limit
  local name=$1 loc=$2 lim=$3 lf=$S/logs/run-$1.log t=$(date +%s)
  rm -rf $S/out-ios; log "$name ($loc) started, limit ${lim}s; $(snap)"
  perl -e 'setpgrp(0,0); alarm shift; exec @ARGV' $lim $SF run $S/shotfleet.toml --platform ios --locales $loc --parallel 1 > $lf 2>&1 &
  RUNPG=$!
  local last=$(date +%s) lastsz=0 killed=0
  while kill -0 $RUNPG 2>/dev/null; do
    sleep 20
    local sz=$(( $(stat -f %z $lf) + $(find $S/out-ios -type f 2>/dev/null | wc -l) ))
    if [ "$sz" != "$lastsz" ]; then lastsz=$sz; last=$(date +%s); fi
    if [ $(( $(date +%s) - last )) -ge 600 ]; then log "$name: NO PROGRESS for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ $(date +%s) -ge $DEADLINE ]; then log "$name: 75 min hold limit reached, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
  done
  wait $RUNPG; local rc=$?; RUNPG=""
  echo "rc=$rc killed=$killed" >> $lf
  [ -d $S/out-ios ] && mv $S/out-ios $S/out-$name
  log "$name done rc=$rc killed=$killed wall=$(( $(date +%s) - t ))s; $(grep -E 'captured|free tier' $lf | tail -2 | tr '\n' ' '); $(snap)"
  return $rc
}

n=1
for L2 in hi,tr zh-Hans,pl nl,pt; do
  if [ $(( DEADLINE - $(date +%s) )) -lt 600 ]; then log "less than 10 min of hold left: skipping run$n ($L2)"; n=$((n+1)); continue; fi
  echo "run$n" > $S/chain-iphone.status
  runone iphone-run$n $L2 1800; rc=$?
  while [ $rc -ne 0 ]; do
    echo "failed$n" > $S/chain-iphone.status; log "run$n FAILED: waiting up to 15 min for $S/redo (flow edited, rerun the same pair) / go (next pair) / abort; lock still held"
    W=$(( $(date +%s) + 900 )); act=""
    while [ $(date +%s) -lt $W ]; do
      for a in redo go abort; do [ -f $S/$a ] && { act=$a; rm -f $S/$a; break; }; done
      [ -n "$act" ] && break; sleep 10
    done
    case "$act" in
      redo) if [ $(( DEADLINE - $(date +%s) )) -lt 600 ]; then log "no time left for a redo"; rc=0; else mv $S/out-iphone-run$n $S/out-iphone-run$n-failed$(date +%H%M) 2>/dev/null; mv $S/logs/run-iphone-run$n.log $S/logs/run-iphone-run$n-failed$(date +%H%M).log; runone iphone-run$n $L2 1800; rc=$?; fi;;
      go) rc=0;;
      *) log "no instruction (or abort): stopping and releasing"; exit 5;;
    esac
  done
  n=$((n+1))
  [ -f $S/abort ] && { log "ABORT requested"; break; }
done
log "ALL DEVICE RUNS DONE"
exit 0
