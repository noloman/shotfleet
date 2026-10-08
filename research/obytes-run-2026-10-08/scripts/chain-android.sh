#!/bin/bash
# Obytes starter showcase, ANDROID device job. SELF-STARTING: the moment it holds the lock it runs the English dry run by itself (no external command).
# After that it waits (max 20 min idle) for one line in $S/android.cmd: "run NAME LOCALES" | "end". Trap cleans up on ANY exit.
# Models: showcase-obytes/chain-iphone.sh (start rule, queue-edit.sh, TERM trap) and showcase-kuokka-android/chain-android-run.sh (emulator cleanup).
# QUEUE FILE RULE 6: the queue is edited ONLY through queue-edit.sh. A DONE line must never be written with > or >>.
S=/Users/manu/Developer/shotfleet-rc-build/showcase-obytes
SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
QE=/Users/manu/Developer/shotfleet-rc-build/queue-edit.sh
Q=/tmp/shotfleet-device-queue.md; L=/tmp/shotfleet-devices.lock
MYLINE='- 2026-10-08 17:20 Obytes starter showcase Android (OCR session): same app'
HOLD=3600
export ANDROID_HOME=/Users/manu/Library/Android/sdk
export PATH=$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH
ADB=$ANDROID_HOME/platform-tools/adb; EMU=$ANDROID_HOME/emulator/emulator
cd $S
mkdir -p $S/logs
log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $*" >> $S/progress.log; }
snap() { echo "load=$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print $1}') free%=$(memory_pressure | awk -F': ' '/free percentage/ {print $2}') disk_free_GiB=$(/bin/df -g /Users/manu | awk 'NR==2{print $4}')"; }
HAVE_LOCK=0; RUNPG=""
caffeinate -i -w $$ >/dev/null 2>&1 &
cleanup() {
  trap - EXIT INT TERM
  log "ANDROID CLEANUP start"
  if [ -n "$RUNPG" ] && kill -0 $RUNPG 2>/dev/null; then log "killing my own run group $RUNPG"; kill -TERM -$RUNPG 2>/dev/null; sleep 5; kill -KILL -$RUNPG 2>/dev/null; fi
  if [ $HAVE_LOCK = 1 ]; then
    # emulators: only a serial that was NOT there at lock time and runs my AVD; never pkill qemu, never delete an AVD
    $ADB devices > $S/logs/adb.after.txt 2>&1
    for s in $($ADB devices | awk '/^emulator-/ {print $1}'); do
      grep -q "^$s" $S/logs/adb.before.txt && { log "emulator $s existed at lock time: not touched"; continue; }
      name=$($ADB -s $s emu avd name 2>/dev/null | head -1 | tr -d '\r')
      if [ "$name" = "shotfleet_android" ]; then $ADB -s $s emu kill >/dev/null 2>&1; log "emu kill sent to my $s ($name)"; else log "emulator $s ($name) is not my AVD: not touched"; fi
    done
    sleep 20
    $ADB devices > $S/logs/adb.final.txt 2>&1; $EMU -list-avds > $S/logs/avds.final.txt 2>&1
    ps axo pid,command | grep "[q]emu-system" | cut -c1-200 > $S/logs/qemu.final.txt
    log "after emu kill: adb devices: $(grep -c ^emulator $S/logs/adb.final.txt) emulator(s); qemu processes: $(wc -l < $S/logs/qemu.final.txt); avds: $(tr '\n' ' ' < $S/logs/avds.final.txt)"
    rm -rf $L; date '+%Y-%m-%d %H:%M:%S' > $S/android.lock.t1; log "LOCK RELEASED ($(snap))"
    if sh $QE done "$MYLINE" "- $(date '+%Y-%m-%d %H:%M') Obytes starter showcase Android (OCR session): DONE, lock RELEASED, my emulator shut down"; then log "queue line replaced by DONE line (queue-edit.sh)"; else log "queue-edit.sh FAILED rc=$? (line left as is)"; fi
  fi
  echo finished > $S/chain-android.status
  log "ANDROID CLEANUP end"
}
trap cleanup EXIT
trap 'exit 143' INT TERM   # the signal ends the script; the EXIT trap does the cleanup
echo waiting > $S/chain-android.status
log "chain-android started pid $$ (waiting for the start rule: lock free, earlier queue lines done, quiet check x3 60 s apart; up to 4 h)"

# ---- start rule ----
earlier_pending() { # lines above mine that are not DONE / MOVED / REMOVED / NOTE / RELEASED / restored / gave up / served
  awk -v my="$MYLINE" 'index($0,my)==1 {exit} /^- / && !/: DONE|: lock RELEASED|\): lock RELEASED|[.] Lock RELEASED|MOVED|REMOVED|NOTE|gave up|\(restored|: served/ {print}' $Q
}
GIVEUP=$(( $(date +%s) + 4*3600 )); ok=0; lastmsg=""
note() { [ "$1" != "$lastmsg" ] && { log "$1"; lastmsg="$1"; }; }
while :; do
  if [ $(date +%s) -ge $GIVEUP ]; then log "GAVE UP after 4 h: start rule never held; queue line left in place"; echo gaveup > $S/chain-android.status; exit 7; fi
  ep=$(earlier_pending)
  if [ -d $L ]; then ok=0; note "wait: lock held by: $(cat $L/holder 2>/dev/null | cut -c1-90)"; sleep 60; continue; fi
  if [ -n "$ep" ]; then ok=0; note "wait: earlier queue line(s) not DONE: $(echo "$ep" | cut -c1-70 | tr '\n' '|')"; sleep 60; continue; fi
  out=$(sh /tmp/shotfleet-quiet-check.sh); rc=$?
  if [ $rc -eq 0 ]; then ok=$((ok+1)); log "quiet check $ok/3 rc=0 '$out' $(snap)"; lastmsg=""; else ok=0; note "quiet check rc=$rc '$out' $(snap)"; fi
  if [ $ok -ge 3 ]; then
    if mkdir $L 2>/dev/null; then
      T0=$(date +%s); HAVE_LOCK=1
      echo "Obytes starter showcase Android (OCR session) | shotfleet 0.1.6 on obytes v9.0.0 Release APK, 1 emulator | started $(date +%H:%M) | est. 20 min, hard limit 60" > $L/holder
      $ADB devices > $S/logs/adb.before.txt 2>&1; $EMU -list-avds > $S/logs/avds.before.txt 2>&1
      ps axo pid,command | grep "[q]emu-system" | cut -c1-200 > $S/logs/qemu.before.txt
      date '+%Y-%m-%d %H:%M:%S' > $S/android.lock.t0
      log "LOCK TAKEN at $(date '+%H:%M:%S') ($(snap)); avds: $(tr '\n' ' ' < $S/logs/avds.before.txt); adb: $(grep -c ^emulator $S/logs/adb.before.txt) emulators; qemu: $(wc -l < $S/logs/qemu.before.txt)"
      break
    else ok=0; log "mkdir lock failed (someone took it)"; fi
  fi
  sleep 60
done
DEADLINE=$(( T0 + HOLD ))

HIGH=0
runone() { # name locales
  local name=$1 loc=$2 lf=$S/logs/run-$1.log t=$(date +%s) hm=$(date +%H%M) lim=1800 left
  left=$(( DEADLINE - t )); [ $left -lt 1900 ] && lim=$((left-60))
  if [ $lim -lt 300 ]; then log "$name: not enough hold time left ($left s): not starting"; return 9; fi
  [ -d $S/out-android ] && mv $S/out-android $S/out-android.prev$hm
  [ -d $S/out-$name ] && mv $S/out-$name $S/out-$name-failed-$hm
  [ -f $lf ] && mv $lf $S/logs/run-$name-failed-$hm.log
  cp $S/flow.android.yaml $S/logs/flow.android.used-by-$name-$hm.yaml
  log "$name ($loc) started, limit ${lim}s, flow sha $(shasum -a 256 $S/flow.android.yaml | cut -c1-12); $(snap)"
  perl -e 'setpgrp(0,0); alarm shift; exec @ARGV' $lim $SF run $S/shotfleet.android.toml --platform android --locales $loc --parallel 1 > $lf 2>&1 &
  RUNPG=$!; local last=$(date +%s) lastsz=0 killed=0 tick=0
  while kill -0 $RUNPG 2>/dev/null; do
    sleep 20; tick=$((tick+1))
    local sz=$(( $(stat -f %z $lf) + $(find $S/out-android -type f 2>/dev/null | wc -l) ))
    if [ "$sz" != "$lastsz" ]; then lastsz=$sz; last=$(date +%s); fi
    if [ $(( $(date +%s) - last )) -ge 600 ]; then log "$name: NO PROGRESS for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ $(date +%s) -ge $DEADLINE ]; then log "$name: 60 min hold limit reached, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=1; break; fi
    if [ "$(sysctl -n vm.loadavg | tr -d '{}' | awk '{print int($1)}')" -gt 600 ]; then HIGH=$((HIGH+1)); else HIGH=0; fi
    if [ $HIGH -ge 30 ]; then log "$name: load > 600 for 10 min, killing my run group"; kill -TERM -$RUNPG; sleep 5; kill -KILL -$RUNPG 2>/dev/null; killed=2; break; fi
    [ $((tick % 15)) = 0 ] && log "$name: progress check $(( ($(date +%s)-t)/60 )) min in: $(snap); adb: $($ADB devices | awk '/^emulator-/ {printf "%s ", $0}'); lines in log: $(wc -l < $lf), files in out: $(find $S/out-android -type f 2>/dev/null | wc -l)"
  done
  wait $RUNPG; local rc=$?
  kill -TERM -$RUNPG 2>/dev/null   # leftovers of my own run group (alarm kills only the leader)
  RUNPG=""
  echo "rc=$rc killed=$killed" >> $lf
  if [ -d $S/out-android ]; then
    if [ $rc -eq 0 ]; then mv $S/out-android $S/out-$name; else mv $S/out-android $S/out-$name-failed-$hm; fi
  fi
  local w=$(( $(date +%s) - t ))
  log "$name done rc=$rc killed=$killed wall=${w}s; $(grep -E 'captured|free tier' $lf | tail -3 | tr '\n' ' '); $(snap)"
  echo "$name $rc $killed $w" > $S/last.result.android
  return $rc
}

# ---- SELF-STARTING: English dry run right now, no command needed ----
echo "running-android-dry" > $S/chain-android.status
runone android-dry en
echo idle > $S/chain-android.status
log "dry run finished: lock still held; waiting up to 20 min for $S/android.cmd ('run NAME LOCALES' | 'end')"

IDLEMAX=1200; lastcmd=$(date +%s)
while :; do
  if [ $(date +%s) -ge $DEADLINE ]; then log "hold limit reached: releasing"; break; fi
  if [ $(( $(date +%s) - lastcmd )) -ge $IDLEMAX ]; then log "no command for $((IDLEMAX/60)) min: releasing"; break; fi
  if [ -f $S/android.cmd ]; then
    c=$(cat $S/android.cmd); rm -f $S/android.cmd; lastcmd=$(date +%s)
    set -- $c
    case "$1" in
      run) echo "running-$2" > $S/chain-android.status; runone "$2" "$3"; echo "idle" > $S/chain-android.status; lastcmd=$(date +%s); log "$2 finished: waiting for the next android.cmd";;
      end) log "end requested"; break;;
      *) log "unknown cmd '$c'";;
    esac
  fi
  sleep 5
done
log "ALL ANDROID DEVICE RUNS DONE"
exit 0
