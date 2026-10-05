#!/bin/zsh
# R2c part (a), approved by the coordinator to run BESIDE the lock holder (an iOS job); I do not take the lock.
# Preconditions (checked, retried every 30 s for up to 10 min): free memory >= 40 %, load < 200, swap < 12 GB, no other qemu-system process.
# Hard limit 15 min. Abort (kill ONLY the descendants of my own run, by exact pid) if load > 400 or free memory < 25 %.
R=<scratch>; exec >> $R/c2a-supervisor.log 2>&1
vals() { python3 - <<'PY'
import re,subprocess,os
m=subprocess.run(['memory_pressure'],capture_output=True,text=True).stdout
mem=int(re.search(r'free percentage:\s*(\d+)%',m).group(1))
load=int(float(os.getloadavg()[0]))
s=subprocess.run(['sysctl','-n','vm.swapusage'],capture_output=True,text=True).stdout
u=re.search(r'used = ([\d.]+)([MG])',s); swap=float(u.group(1))/(1024 if u.group(2)=='M' else 1)
print(mem,load,round(swap,1))
PY
}
desc() { local p=$1; for c in $(pgrep -P $p); do echo $c; desc $c; done; }
start=$(date +%s)
while true; do
  read mem load swap <<< "$(vals)"; others=$(pgrep -f 'qemu-system' | wc -l | tr -d ' ')
  echo "$(date +%T) precheck mem=${mem}% load=$load swap=${swap}G emulators=$others"
  [ $mem -ge 40 ] && [ $load -lt 200 ] && [ ${swap%.*} -lt 12 ] && [ "$others" = 0 ] && break
  [ $(( $(date +%s)-start )) -ge 600 ] && { echo "$(date +%T) preconditions not met within 10 min: not started"; echo NOTSTARTED; exit 2; }
  sleep 30
done
echo "$(date +%T) STARTING R2c(a) beside the lock holder (no lock taken)"
$R/c2a.sh > $R/c2a.out 2>&1 &
RP=$!; t0=$(date +%s); reason=""
while kill -0 $RP 2>/dev/null; do
  sleep 10; read mem load swap <<< "$(vals)"; el=$(( $(date +%s)-t0 ))
  echo "$(date +%T) heartbeat t=${el}s mem=${mem}% load=$load swap=${swap}G run.log=$(wc -l < $R/c2android/run.log 2>/dev/null | tr -d ' ') lines"
  [ $load -gt 400 ] && reason="load $load > 400"; [ $mem -lt 25 ] && reason="free memory ${mem}% < 25%"; [ $el -ge 900 ] && reason="hard limit 15 min"
  if [ -n "$reason" ]; then echo "$(date +%T) ABORT: $reason; killing my run tree (exact pids)"; D=$(desc $RP); kill $D $RP 2>/dev/null; sleep 5; kill -9 $D $RP 2>/dev/null; echo "ABORTED: $reason" >> $R/c2a.out; break; fi
done
wait $RP 2>/dev/null; echo "$(date +%T) R2c(a) over (reason='${reason:-finished}'); leftover qemu: $(pgrep -f qemu-system | wc -l | tr -d ' ')"
echo C2ADONE
