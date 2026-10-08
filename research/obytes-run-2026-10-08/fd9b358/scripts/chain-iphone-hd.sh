#!/bin/bash
# Obytes starter showcase, iPhone RE-RUN on upstream commit fd9b358. SELF-STARTING chain:
# start rule -> lock -> English dry run at once -> counted run en,ar -> optional repeat ar,en -> cleanup. No external command needed.
# Control files (all optional): hd.abort = stop now (kills only my own run group, releases); cmd.hd = "run NAME LOCALES" | "release"
# (only read after a failed step, as the fix-and-retry channel). QUEUE FILE RULE 6: edited ONLY through queue-edit.sh.
S=/Users/manu/Developer/shotfleet-rc-build/showcase-obytes
SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
QE=/Users/manu/Developer/shotfleet-rc-build/queue-edit.sh
Q=/tmp/shotfleet-device-queue.md; L=/tmp/shotfleet-devices.lock
MYLINE='- 2026-10-08 19:17 Obytes starter showcase RE-RUN iPhone'
SIM=shotfleet-iphone-17-pro-max-1
LG=$S/logs-fd9b358
HOLD=3600
cd $S || exit 9
mkdir -p $LG
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') [ios-hd] $*" >> $S/progress.log; }
snap() { echo "load=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print $1}') free%=$(memory_pressure | awk -F': ' '/free percentage/ {print $2}') swap=$(sysctl -n vm.swapusage | awk '{print $6,$7,$8,$9}' | tr -d ' ') disk_free_GiB=$(/bin/df -g /Users/manu | awk 'NR==2{print $4}')"; }
HAVE_LOCK=0; RUNPG=""
rm -f $S/hd.abort
caffeinate -i -w $$ >/dev/null 2>&1 &
cleanup() {
  trap - EXIT INT TERM
  log "CLEANUP start"
  if [ -n "$RUNPG" ] && kill -0 $RUNPG 2>/dev/null; then log "killing my own run group $RUNPG"; kill -TERM -$RUNPG 2>/dev/null; sleep 5; kill -KILL -$RUNPG 2>/dev/null; fi
  if [ $HAVE_LOCK = 1 ]; then
    # shut down (never delete) only shotfleet-* simulators that were not Booted at lock time and are Booted now. Never the owner's iPhone 15 Pro.
    xcrun simctl list devices > $LG/hd-sims.after.txt 2>&1
    for u in $(grep -oE '[0-9A-F]{8}-[0-9A-F-]{27}' $LG/hd-sims.after.txt | sort -u); do
      line=$(grep "$u" $LG/hd-sims.after.txt)
      case "$line" in *shotfleet-*) ;; *) continue;; esac
      echo "$line" | grep -q Booted || continue
      if grep "$u" $LG/hd-sims.before.txt | grep -q Booted; then log "sim $u was already Booted at lock time: not mine, left alone"; continue; fi
      xcrun simctl shutdown $u 2>/dev/null; log "shut down $u (booted during my hold): $line"
    done
    sleep 3
    xcrun simctl list devices > $LG/hd-sims.final.txt 2>&1
    rm -rf $L; log "LOCK RELEASED ($(snap))"
    if sh $QE done "$MYLINE" "- $(date '+%Y-%m-%d %H:%M') Obytes starter showcase RE-RUN iPhone (OCR session): DONE, lock RELEASED, my simulators shut down"; then log "queue line replaced by DONE line (queue-edit.sh)"; else log "queue-edit.sh FAILED rc=$? (line left as is)"; fi
    echo released > $S/chain-iphone-hd.status
  fi
  log "CLEANUP end"
}
trap cleanup EXIT
trap 'exit 143' INT TERM
echo waiting > $S/chain-iphone-hd.status
log "chain-iphone-hd started pid $$ (waiting for the start rule: lock free, every earlier queue line DONE, quiet check x3 60 s apart; gives up after 5 h)"

earlier_pending() {
  awk -v my="$MYLINE" 'index($0,my)==1 {exit} /^- / && !/: DONE|DONE [0-9]|DONE,|lock RELEASED|REMOVED|MOVED|NOTE|gave up|\(restored|: served/ {print}' $Q
}
GIVEUP=$(( $(date +%s) + 5*3600 )); ok=0
while :; do
  if [ $(date +%s) -ge $GIVEUP ]; then log "GAVE UP after 5 h: start rule never held; queue line left in place"; echo gaveup > $S/chain-iphone-hd.status; exit 7; fi
  ep=$(earlier_pending)
  if [ -d $L ]; then ok=0; log "wait: lock held by: $(cat $L/holder 2>/dev/null | cut -c1-90)"; sleep 60; continue; fi
  if [ -n "$ep" ]; then ok=0; log "wait: earlier queue line(s) not DONE: $(echo "$ep" | cut -c1-70 | tr '\n' '|')"; sleep 60; continue; fi
  out=$(sh /tmp/shotfleet-quiet-check.sh); rc=$?
  if [ $rc -eq 0 ]; then ok=$((ok+1)); log "quiet check $ok/3 rc=0 '$out' $(snap)"; else ok=0; log "quiet check rc=$rc '$out' $(snap)"; fi
  if [ $ok -ge 3 ]; then
    if mkdir $L 2>/dev/null; then
      T0=$(date +%s); HAVE_LOCK=1
      echo "Obytes starter showcase RE-RUN iPhone (OCR session) | shotfleet 0.1.6 on obytes fd9b358 Release, iOS 26.4, 1 simulator | started $(date +%H:%M) | est. 15 min, hard limit 60" > $L/holder
      xcrun simctl list devices > $LG/hd-sims.before.txt 2>&1
      log "LOCK TAKEN at $(date '+%H:%M:%S') ($(snap)); hd-sims.before saved"
      break
    else ok=0; log "mkdir lock failed (someone took it)"; fi
  fi
  sleep 60
done
DEADLINE=$(( T0 + HOLD ))
echo "$T0" > $S/lock.t0.hd
echo running > $S/chain-iphone-hd.status

nfail=0
# runone NAME LOCALES LIMIT NUMPNG ; output of shotfleet is out-ios-hd, moved to out-ios-hd-NAME (or out-ios-hd-NAME-failed-N)
runone() {
  local name=$1 loc=$2 lim=$3 want=$4 lf=$LG/run-ios-hd-$1.log t=$(date +%s)
  if [ -e $S/out-ios-hd ]; then log "$name: out-ios-hd exists before start (not mine?): refusing"; return 8; fi
  cp $S/shotfleet.ios.hd.toml $LG/shotfleet.ios.hd.$name.toml; cp $S/flow.ios.hd.yaml $LG/flow.ios.hd.$name.yaml
  log "$name ($loc) started, limit ${lim}s, flow sha $(shasum -a 256 $S/flow.ios.hd.yaml | cut -c1-12); $(snap)"
  perl -e 'setpgrp(0,0); alarm shift; exec @ARGV' $lim $SF run $S/shotfleet.ios.hd.toml --platform ios --locales $loc --parallel 1 > $lf 2>&1 &
  RUNPG=$!
  local last=$(date +%s) lastsz=0 killed=0 hi=0
  while kill -0 $RUNPG 2>/dev/null; do
    sleep 20
    local sz=$(( $(stat -f %z $lf) + $(find $S/out-ios-hd -type f 2>/dev/null | wc -l) ))
    if [ "$sz" != "$lastsz" ]; then lastsz=$sz; last=$(date +%s); log "$name: progress (log $(stat -f %z $lf) bytes, $(find $S/out-ios-hd -name '*.png' 2>/dev/null | wc -l) png)"; fi
    if [ $(( $(date +%s) - last )) -ge 600 ]; then log "$name: NO PROGRESS for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ $(date +%s) -ge $DEADLINE ]; then log "$name: hold limit reached, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ -f $S/hd.abort ]; then log "$name: hd.abort found, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=3; break; fi
    if [ "$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print int($1)}')" -gt 600 ]; then hi=$((hi+1)); else hi=0; fi
    if [ $hi -ge 30 ]; then log "$name: load > 600 for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=2; break; fi
  done
  wait $RUNPG; local rc=$?
  kill -TERM -$RUNPG 2>/dev/null
  RUNPG=""
  echo "rc=$rc killed=$killed" >> $lf
  local npng=0
  [ -d $S/out-ios-hd ] && npng=$(find $S/out-ios-hd/raw -name '*.png' 2>/dev/null | wc -l | tr -d ' ')
  local good=0; [ $rc -eq 0 ] && [ $killed -eq 0 ] && [ "$npng" -eq "$want" ] && good=1
  if [ -d $S/out-ios-hd ]; then
    if [ $good = 1 ]; then mv $S/out-ios-hd $S/out-ios-hd-$name
    else nfail=$((nfail+1)); mv $S/out-ios-hd $S/out-ios-hd-$name-failed-$nfail; fi
  fi
  local w=$(( $(date +%s) - t ))
  log "$name done rc=$rc killed=$killed png=$npng/$want good=$good wall=${w}s; $(grep -E 'captured|free tier' $lf | tail -3 | tr '\n' ' '); $(snap)"
  echo "$name $rc $killed $w png=$npng good=$good" > $S/last.result.hd
  [ $good = 1 ]
}
limit_now() { local left=$(( DEADLINE - $(date +%s) )); local lim=1800; [ $left -lt 1900 ] && lim=$((left-60)); echo $lim; }

# ---- automatic plan: no external command needed ----
FAILED=0
for step in dry:en:6 run1:en,ar:12 run2:ar,en:12; do
  name=${step%%:*}; rest=${step#*:}; loc=${rest%%:*}; want=${rest##*:}
  [ -f $S/hd.abort ] && { log "hd.abort found: stopping plan"; break; }
  if [ "$name" = run2 ] && [ $(( $(date +%s) - T0 )) -gt 2400 ]; then log "run2 skipped: more than 40 min of the hold used"; break; fi
  lim=$(limit_now); [ $lim -lt 300 ] && { log "$name: not enough hold time left, releasing"; break; }
  echo "running $name" > $S/chain-iphone-hd.status
  runone $name $loc $lim $want || { FAILED=1; log "$name FAILED: automatic plan stops; waiting up to 12 min for cmd.hd (run NAME LOCALES | release)"; break; }
done
if [ $FAILED = 1 ]; then
  lastcmd=$(date +%s)
  echo "failed-waiting" > $S/chain-iphone-hd.status
  while :; do
    [ $(date +%s) -ge $DEADLINE ] && { log "hold limit reached: releasing"; break; }
    [ -f $S/hd.abort ] && { log "hd.abort: releasing"; break; }
    [ $(( $(date +%s) - lastcmd )) -ge 720 ] && { log "no command for 12 min after a failure: releasing"; break; }
    if [ -f $S/cmd.hd ]; then
      c=$(cat $S/cmd.hd); rm -f $S/cmd.hd; lastcmd=$(date +%s); set -- $c
      case "$1" in
        run) lim=$(limit_now); [ $lim -lt 300 ] && { log "cmd '$c': not enough hold time left"; break; }
             n=$(echo $3 | awk -F, '{print NF*6}')
             echo "running $2" > $S/chain-iphone-hd.status; runone "$2" "$3" $lim $n; echo failed-waiting > $S/chain-iphone-hd.status; lastcmd=$(date +%s);;
        release) log "cmd release"; break;;
        *) log "unknown cmd '$c'";;
      esac
    fi
    sleep 5
  done
fi
log "plan finished, releasing"
exit 0
