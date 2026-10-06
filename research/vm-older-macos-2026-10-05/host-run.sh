#!/bin/sh
# One VM cycle: gate check -> pull/clone -> run headless -> copy in + run guest-test.sh over SSH -> collect -> stop -> delete VM and image.
#   sh host-run.sh ghcr.io/cirruslabs/macos-tahoe-vanilla:26.2 sf-262
#   sh host-run.sh --gate        # only print the gate check (exit 0 = all clear)
# Image login admin/admin is the Cirrus image's documented default (never the owner's credentials).
# Hard limit 45 min for the whole cycle; on timeout it kills ONLY the tart pids it started (by exact pid) and deletes the VM.
D=/Users/manu/Developer/shotfleet-rc-build/vm-test
export TART_HOME=$D/tart-home; TART=$D/tart/tart.app/Contents/MacOS/tart
LOG=$D/progress.log; mkdir -p "$D/results" "$TART_HOME"
log() { echo "$(date '+%F %T') $*" | tee -a "$LOG"; }

gate() {  # all must hold before a pull
  ok=0
  h=$(cat /tmp/shotfleet-devices.lock/holder 2>/dev/null)
  [ -n "$h" ] && { echo "gate: lock held: $h"; ok=1; }
  [ -e /tmp/shotfleet-devices.lock ] && { echo "gate: /tmp/shotfleet-devices.lock exists"; ok=1; }
  grep -q "Job 3 device work DONE" /Users/manu/Developer/shotfleet-rc-build/device-slots/RESUME.md \
    || { echo "gate: Job 3 not reported done in device-slots/RESUME.md"; ok=1; }
  l=$(sysctl -n vm.loadavg | awk '{print int($2)}'); [ "$l" -lt 300 ] || { echo "gate: load $l >= 300"; ok=1; }
  grep -q "lock released" /Users/manu/Developer/shotfleet-rc-build/0.1.3/g3-013d.log 2>/dev/null || { echo "gate: 0.1.3 gate rerun not finished (g3-013d.log)"; ok=1; }
  sw=$(memory_pressure 2>/dev/null | awk -F': ' '/free percentage/{print int($2)}'); [ "${sw:-0}" -ge 30 ] || { echo "gate: memory free ${sw}% < 30"; ok=1; }
  f=$(df -g / | awk 'NR==2{print $4}'); [ "$f" -ge 70 ] || { echo "gate: free disk ${f} GB < 70 (VM needs ~25-30 GB, floor 40)"; ok=1; }
  echo "gate: load=$l memfree=${sw}% free=${f}GB lock='${h:-none}' -> $([ $ok = 0 ] && echo CLEAR || echo WAIT)"
  return $ok
}
[ "$1" = --gate ] && { gate; exit $?; }

IMG=$1; N=$2; [ -n "$IMG" ] && [ -n "$N" ] || { echo "usage: host-run.sh IMAGE NAME | --gate" >&2; exit 2; }
gate || { log "$N: gate not clear, not starting"; exit 3; }
OUT=$D/results/$N.txt; START=$(date +%s); PIDS=$D/results/$N.pids; : > "$PIDS"
log "$N: START $IMG, disk free $(df -g / | awk 'NR==2{print $4}') GB"

cleanup() {
  for p in $(cat "$PIDS" 2>/dev/null); do kill "$p" 2>/dev/null; done   # only our own, by exact pid
  "$TART" stop "$N" >/dev/null 2>&1; sleep 3
  for p in $(cat "$PIDS" 2>/dev/null); do kill -9 "$p" 2>/dev/null; done
  "$TART" delete "$N" 2>&1 | tail -1; "$TART" delete "$IMG" 2>&1 | tail -1
  "$TART" prune --entries=caches --older-than=0 >/dev/null 2>&1
  log "$N: deleted VM and image; tart list: $("$TART" list 2>&1 | tail -n +2 | wc -l | tr -d ' ') entries; TART_HOME $(du -sh "$TART_HOME" | cut -f1); disk free $(df -g / | awk 'NR==2{print $4}') GB; cycle $(( ($(date +%s) - START) / 60 )) min"
}
# watchdog: 45 min for the whole cycle, then kill our own tart pids (the main flow then cleans up)
( t=0; while [ $t -lt 2700 ]; do sleep 15; t=$((t+15)); f=$(df -g / | awk 'NR==2{print $4}'); [ "$f" -lt 40 ] && { log "$N: free disk ${f} GB < 40, aborting"; break; }; done
  [ $t -ge 2700 ] && log "$N: 45 min limit reached, killing own tart pids"; for p in $(cat "$PIDS"); do kill "$p" 2>/dev/null; done ) &
WD=$!
trap 'kill $WD 2>/dev/null; cleanup' EXIT

"$TART" clone "$IMG" "$N" > "$D/results/$N.pull.log" 2>&1 & echo $! >> "$PIDS"; wait $!; rc=$?
log "$N: clone rc=$rc in $(( ($(date +%s) - START) / 60 )) min; $(du -sh "$TART_HOME" | cut -f1) on disk"
[ $rc = 0 ] || exit 1
"$TART" set "$N" --cpu 4 --memory 6144
"$TART" run --no-graphics "$N" > "$D/results/$N.run.log" 2>&1 & echo $! >> "$PIDS"
IP=$("$TART" ip --wait 180 "$N" 2>/dev/null); log "$N: running, ip=${IP:-none}"
[ -n "$IP" ] || exit 1

# password auth with the image default admin/admin via SSH_ASKPASS (no extra tool)
printf '#!/bin/sh\necho admin\n' > "$D/askpass.sh"; chmod +x "$D/askpass.sh"
export SSH_ASKPASS=$D/askpass.sh SSH_ASKPASS_REQUIRE=force DISPLAY=:0
SO="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=10"
i=0; until ssh $SO admin@"$IP" true 2>/dev/null; do i=$((i+1)); [ $i -gt 30 ] && { log "$N: ssh never came up"; exit 1; }; sleep 5; done
ssh $SO admin@"$IP" 'mkdir -p sf-in/samples/de sf-in/samples/ca'
scp $SO -q "$D/guest-test.sh" "$D/selftest.sh" admin@"$IP":sf-in/
scp $SO -q "$D/samples/de/02_advanced.png" admin@"$IP":sf-in/samples/de/
scp $SO -q "$D/samples/ca/02_advanced.png" admin@"$IP":sf-in/samples/ca/
log "$N: guest test start"
ssh $SO admin@"$IP" 'sh sf-in/guest-test.sh' > "$OUT" 2>&1 & echo $! >> "$PIDS"; wait $!
log "$N: guest test done"; grep '^R ' "$OUT" | tee -a "$LOG"
