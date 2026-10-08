#!/bin/bash
# wger showcase, iPhone device job. Start rule -> lock -> command loop (runs on request) -> always cleans up.
# Commands arrive as one line in $S/cmd:  "run NAME LOCALES"  |  "release".  Result of the last run: $S/last.result ("NAME rc killed wall").
# Pattern from showcase-wod/chain-iphone2.sh (trap, per-run alarm, own process group only, 10 min no-progress, 75 min hold).
S=/Users/manu/Developer/shotfleet-rc-build/showcase-wger
SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
Q=/tmp/shotfleet-device-queue.md; L=/tmp/shotfleet-devices.lock
MYLINE='- 2026-10-08 08:57 wger showcase iPhone'
cd $S
mkdir -p $S/logs
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $S/progress.log; }
snap() { echo "load=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print $1}') free%=$(memory_pressure | awk -F': ' '/free percentage/ {print $2}') disk_free_GiB=$(/bin/df -g /Users/manu | awk 'NR==2{print $4}')"; }
HAVE_LOCK=0; RUNPG=""
cleanup() {
  trap - EXIT INT TERM
  log "CLEANUP start"
  if [ -n "$RUNPG" ] && kill -0 $RUNPG 2>/dev/null; then log "killing my own run group $RUNPG"; kill -TERM -$RUNPG 2>/dev/null; sleep 5; kill -KILL -$RUNPG 2>/dev/null; fi
  if [ $HAVE_LOCK = 1 ]; then
    # simulators: only what became booted/new during my hold. Pool sims that existed before are shut down (never deleted); new ones are shut down + deleted.
    xcrun simctl list devices > $S/logs/sims.after.txt 2>&1
    for u in $(grep -oE '[0-9A-F]{8}-[0-9A-F-]{27}' $S/logs/sims.after.txt | sort -u); do
      line=$(grep "$u" $S/logs/sims.after.txt)
      case "$line" in *shotfleet-*) ;; *) continue;; esac
      if grep -q "$u" $S/logs/sims.before.txt; then
        if ! grep "$u" $S/logs/sims.before.txt | grep -q Booted && echo "$line" | grep -q Booted; then xcrun simctl shutdown $u 2>/dev/null; log "shut down $u (pool sim, existed before, was shut down at lock time)"; fi
      else
        xcrun simctl shutdown $u 2>/dev/null; xcrun simctl delete $u 2>/dev/null; log "shut down + deleted NEW simulator $u"
      fi
    done
    sleep 3
    xcrun simctl list devices > $S/logs/sims.final.txt 2>&1
    rm -rf $L; log "LOCK RELEASED ($(snap))"
    python3 - <<PY
p="$Q"; t=open(p).read().split("\n")
t=[l for l in t if not l.startswith("$MYLINE")]
while t and t[-1]=="": t.pop()
t.append("- $(date '+%Y-%m-%d %H:%M') wger showcase iPhone (OCR session): DONE, lock RELEASED, my simulators shut down")
open(p,"w").write("\n".join(t)+"\n")
PY
    log "queue line replaced by DONE line"
    echo released > $S/chain-iphone.status
  fi
  log "CLEANUP end"
}
trap cleanup EXIT INT TERM
echo waiting > $S/chain-iphone.status
log "chain-iphone started pid $$ (waiting for the start rule: lock free, earlier queue lines done, quiet check x3 60 s apart)"

# ---- start rule ----
earlier_pending() { # earlier queue lines that are not DONE/REMOVED/NOTE/RELEASED/gave up ("2026-10-07 00:16" = stale, same agent posted DONE three times since)
  awk -v my="$MYLINE" 'index($0,my)==1 {exit} /^- / && !/DONE|REMOVED|NOTE|RELEASED|gave up|2026-10-07 00:16/ {print}' $Q
}
GIVEUP=$(( $(date +%s) + 3*3600 )); ok=0
while :; do
  if [ $(date +%s) -ge $GIVEUP ]; then log "GAVE UP after 3 h: start rule never held; queue line left in place"; echo gaveup > $S/chain-iphone.status; exit 7; fi
  ep=$(earlier_pending)
  if [ -d $L ]; then ok=0; log "wait: lock held by: $(cat $L/holder 2>/dev/null)"; sleep 60; continue; fi
  if [ -n "$ep" ]; then ok=0; log "wait: earlier queue line(s) not DONE: $(echo "$ep" | cut -c1-80 | tr '\n' '|')"; sleep 60; continue; fi
  out=$(sh /tmp/shotfleet-quiet-check.sh); rc=$?
  if [ $rc -eq 0 ]; then ok=$((ok+1)); log "quiet check $ok/3 rc=0 '$out' $(snap)"; else ok=0; log "quiet check rc=$rc '$out' $(snap)"; fi
  if [ $ok -ge 3 ]; then
    if mkdir $L 2>/dev/null; then
      T0=$(date +%s); HAVE_LOCK=1
      echo "wger showcase iPhone (OCR session) | shotfleet 0.1.6 on wger 2.1.1 debug, iOS 26.4, 1 simulator | started $(date +%H:%M) | est. 30 min, hard limit 75" > $L/holder
      xcrun simctl list devices > $S/logs/sims.before.txt 2>&1
      log "LOCK TAKEN at $(date '+%H:%M:%S') ($(snap)); sims.before saved"
      break
    else ok=0; log "mkdir lock failed (someone took it)"; fi
  fi
  sleep 60
done
DEADLINE=$(( T0 + 75*60 ))
echo "$T0" > $S/lock.t0
echo idle > $S/chain-iphone.status

runone() { # name locales limit
  local name=$1 loc=$2 lim=$3 lf=$S/logs/run-$1.log t=$(date +%s)
  rm -rf $S/out-ios; log "$name ($loc) started, limit ${lim}s; $(snap)"
  perl -e 'setpgrp(0,0); alarm shift; exec @ARGV' $lim $SF run $S/shotfleet.toml --platform ios --locales $loc --parallel 1 > $lf 2>&1 &
  RUNPG=$!
  local last=$(date +%s) lastsz=0 killed=0 hi=0
  while kill -0 $RUNPG 2>/dev/null; do
    sleep 20
    local sz=$(( $(stat -f %z $lf) + $(find $S/out-ios -type f 2>/dev/null | wc -l) ))
    if [ "$sz" != "$lastsz" ]; then lastsz=$sz; last=$(date +%s); fi
    if [ $(( $(date +%s) - last )) -ge 600 ]; then log "$name: NO PROGRESS for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ $(date +%s) -ge $DEADLINE ]; then log "$name: 75 min hold limit reached, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ "$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print int($1)}')" -gt 600 ]; then hi=$((hi+1)); else hi=0; fi
    if [ $hi -ge 30 ]; then log "$name: load > 600 for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=2; break; fi
  done
  wait $RUNPG; local rc=$?; RUNPG=""
  echo "rc=$rc killed=$killed" >> $lf
  [ -d $S/out-ios ] && mv $S/out-ios $S/out-$name
  local w=$(( $(date +%s) - t ))
  log "$name done rc=$rc killed=$killed wall=${w}s; $(grep -E 'captured|free tier' $lf | tail -3 | tr '\n' ' '); $(snap)"
  echo "$name $rc $killed $w" > $S/last.result
  return $rc
}

IDLEMAX=1500; lastcmd=$(date +%s)
while :; do
  if [ $(date +%s) -ge $DEADLINE ]; then log "75 min hold limit reached: releasing"; break; fi
  if [ $(( $(date +%s) - lastcmd )) -ge $IDLEMAX ]; then log "no command for $((IDLEMAX/60)) min: releasing"; break; fi
  if [ -f $S/cmd ]; then
    c=$(cat $S/cmd); rm -f $S/cmd; lastcmd=$(date +%s)
    set -- $c
    case "$1" in
      run) left=$(( DEADLINE - $(date +%s) )); lim=1800; [ $left -lt 1900 ] && lim=$((left-60))
           if [ $lim -lt 300 ]; then log "cmd '$c': not enough hold time left ($left s), releasing"; break; fi
           echo "running $2" > $S/chain-iphone.status; runone "$2" "$3" $lim; echo "idle" > $S/chain-iphone.status; lastcmd=$(date +%s);;
      release) log "cmd release"; break;;
      *) log "unknown cmd '$c'";;
    esac
  fi
  sleep 5
done
exit 0
