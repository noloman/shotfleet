#!/bin/bash
# WOD Tracker showcase, Android device job. Waits for queue/quiet(3x)/lock, then runs what $S/android.cmd says ("run NAME LOCALES" / "end"), always cleans up.
S=/Users/manu/Developer/shotfleet-rc-build/showcase-wod
SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
Q=/tmp/shotfleet-device-queue.md; L=/tmp/shotfleet-devices.lock
MYLINE='- 2026-10-07 18:06 WOD Tracker showcase Android (OCR session)'
export ANDROID_HOME=/Users/manu/Library/Android/sdk
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
ADB=$ANDROID_HOME/platform-tools/adb; EMU=$ANDROID_HOME/emulator/emulator
cd $S
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $S/progress.log; }
snap() { echo "load=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print $1}') free%=$(memory_pressure | awk -F': ' '/free percentage/ {print $2}') disk_free_GiB=$(/bin/df -g /Users/manu | awk 'NR==2{print $4}')"; }
HAVE_LOCK=0; RUNPG=""
cleanup() {
  trap - EXIT INT TERM
  log "ANDROID CLEANUP start"
  if [ -n "$RUNPG" ] && kill -0 $RUNPG 2>/dev/null; then log "killing my own run group $RUNPG"; kill -TERM -$RUNPG 2>/dev/null; sleep 5; kill -KILL -$RUNPG 2>/dev/null; fi
  if [ $HAVE_LOCK = 1 ]; then
    # emulators: only a serial that was NOT there at lock time and runs my AVD
    $ADB devices > $S/logs/adb.after.txt 2>&1
    for s in $($ADB devices | awk '/^emulator-/ {print $1}'); do
      grep -q "^$s" $S/logs/adb.before.txt && { log "emulator $s existed at lock time: not touched"; continue; }
      name=$($ADB -s $s emu avd name 2>/dev/null | head -1 | tr -d '\r')
      if [ "$name" = "shotfleet_android" ]; then $ADB -s $s emu kill >/dev/null 2>&1; log "emu kill sent to my $s ($name)"; else log "emulator $s ($name) is not my AVD: not touched"; fi
    done
    sleep 20
    $ADB devices > $S/logs/adb.final.txt 2>&1; $EMU -list-avds > $S/logs/avds.final.txt 2>&1
    ps axo pid,command | grep "[q]emu-system" | cut -c1-200 > $S/logs/qemu.final.txt
    log "after emu kill: adb devices: $(grep -c ^emulator $S/logs/adb.final.txt) emulator(s); qemu processes: $(wc -l < $S/logs/qemu.final.txt)"
    rm -rf $L; log "LOCK RELEASED ($(snap))"
    python3 - <<PY
p="$Q"; t=open(p).read().split("\n")
t=[l for l in t if not l.startswith("$MYLINE")]
while t and t[-1]=="": t.pop()
t.append("- $(date '+%Y-%m-%d %H:%M') WOD Tracker showcase Android (OCR session): DONE, lock RELEASED, my emulator shut down")
open(p,"w").write("\n".join(t)+"\n")
PY
    log "queue line replaced by DONE line"
  fi
  echo finished > $S/chain-android-run.status
  log "ANDROID CLEANUP end"
}
trap cleanup EXIT INT TERM
echo waiting > $S/chain-android-run.status
log "chain-android-run started pid $$ (waiting for queue, 3 quiet checks, lock)"

# ---- wait: earlier queue lines done, 3 quiet checks 60 s apart, then mkdir (up to 3 h)
WEND=$(( $(date +%s) + 10800 )); ok=0
while [ $(date +%s) -lt $WEND ]; do
  early=$(awk -v m="$MYLINE" 'index($0,m)==1 {exit} /^- / && !/DONE|NOTE|REMOVED|RELEASED|00:16 remoti screenshot agent/ {print}' $Q)
  if [ -n "$early" ]; then log "earlier queue line(s) still open: $(echo "$early" | head -2 | cut -c1-90)"; sleep 120; ok=0; continue; fi
  if [ -d $L ]; then log "lock held: $(cat $L/holder 2>/dev/null | cut -c1-120)"; sleep 120; ok=0; continue; fi
  if out=$(sh /tmp/shotfleet-quiet-check.sh 2>&1); then ok=$((ok+1)); log "quiet check pass $ok/3: $out; $(snap)"; echo "$(date +%T) $out $(snap)" >> $S/logs/android-quiet.log; else ok=0; log "quiet check FAILED: $out; $(snap)"; sleep 120; continue; fi
  if [ $ok -ge 3 ]; then
    if mkdir $L 2>/dev/null; then HAVE_LOCK=1; break; else log "mkdir failed: someone took the lock"; ok=0; fi
  else sleep 60; fi
done
[ $HAVE_LOCK = 1 ] || { log "never got the lock in 3 h: stopping, queue line left"; exit 8; }
T0=$(date +%s); DEADLINE=$(( T0 + 88*60 ))
echo "WOD Tracker showcase Android (OCR session) | shotfleet 0.1.6 on WOD Tracker 1.6.7 debug APK, 1 emulator | started $(date +%H:%M) | est. 40 min, hard limit 90 (ends $(date -j -r $((T0+90*60)) +%H:%M))" > $L/holder
echo "$(date '+%Y-%m-%d %H:%M:%S')" > $S/android.lock.t0
$ADB devices > $S/logs/adb.before.txt 2>&1; $EMU -list-avds > $S/logs/avds.before.txt 2>&1
ps axo pid,command | grep "[q]emu-system" | cut -c1-200 > $S/logs/qemu.before.txt
log "LOCK TAKEN: $(cat $L/holder); $(snap); avds: $(tr '\n' ' ' < $S/logs/avds.before.txt); adb: $(grep -c ^emulator $S/logs/adb.before.txt) emulators; qemu: $(wc -l < $S/logs/qemu.before.txt)"

# load watchdog: >600 for 10 min => stop
HIGH=0
runone() { # name locales
  local name=$1 loc=$2 lf=$S/logs/run-$1.log t=$(date +%s)
  [ -d $S/out-android ] && mv $S/out-android $S/out-android.prev$(date +%H%M)
  [ -d $S/out-$name ] && mv $S/out-$name $S/out-$name-failed-$(date +%H%M)
  [ -f $lf ] && mv $lf $S/logs/run-$name-failed-$(date +%H%M).log
  log "$name ($loc) started, limit 1800s; $(snap)"
  perl -e 'setpgrp(0,0); alarm shift; exec @ARGV' 1800 $SF run $S/shotfleet.android.toml --platform android --locales $loc --parallel 1 > $lf 2>&1 &
  RUNPG=$!; local last=$(date +%s) lastsz=0 killed=0 tick=0
  while kill -0 $RUNPG 2>/dev/null; do
    sleep 20; tick=$((tick+1))
    local sz=$(( $(stat -f %z $lf) + $(find $S/out-android -type f 2>/dev/null | wc -l) ))
    if [ "$sz" != "$lastsz" ]; then lastsz=$sz; last=$(date +%s); fi
    if [ $(( $(date +%s) - last )) -ge 600 ]; then log "$name: NO PROGRESS for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ $(date +%s) -ge $DEADLINE ]; then log "$name: 88 min hold limit reached, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    ld=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print int($1)}')
    if [ $ld -gt 600 ]; then HIGH=$((HIGH+1)); else HIGH=0; fi
    if [ $HIGH -ge 30 ]; then log "$name: load > 600 for 10 min, stopping my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    [ $((tick % 15)) = 0 ] && log "$name: progress check $(( ($(date +%s)-t)/60 )) min in: $(snap); adb: $($ADB devices | awk '/^emulator-/ {printf "%s ", $0}'); lines in log: $(wc -l < $lf), files in out: $(find $S/out-android -type f 2>/dev/null | wc -l)"
  done
  wait $RUNPG; local rc=$?; RUNPG=""
  echo "rc=$rc killed=$killed" >> $lf
  [ -d $S/out-android ] && mv $S/out-android $S/out-$name
  log "$name done rc=$rc killed=$killed wall=$(( $(date +%s) - t ))s; $(grep -E 'captured|free tier' $lf | tail -2 | tr '\n' ' '); $(snap)"
  return $rc
}

runone android-dry en; echo "dry-done" > $S/chain-android-run.status
log "dry run finished: waiting up to 15 min for $S/android.cmd ('run NAME LOCALES' or 'end'); lock still held"
while :; do
  W=$(( $(date +%s) + 900 )); cmd=""
  while [ $(date +%s) -lt $W ]; do [ -f $S/android.cmd ] && { cmd=$(cat $S/android.cmd); rm -f $S/android.cmd; break; }; sleep 5; done
  set -- $cmd
  case "$1" in
    run) if [ $(( DEADLINE - $(date +%s) )) -lt 600 ]; then log "less than 10 min of hold left: not starting $2"; break; fi
         echo "running-$2" > $S/chain-android-run.status; runone $2 $3; rc=$?; echo "done-$2-rc$rc" > $S/chain-android-run.status
         log "$2 finished rc=$rc: waiting up to 15 min for the next android.cmd";;
    end) log "end requested"; break;;
    *) log "no instruction within 15 min: stopping and releasing"; break;;
  esac
done
log "ALL ANDROID DEVICE RUNS DONE"
exit 0
