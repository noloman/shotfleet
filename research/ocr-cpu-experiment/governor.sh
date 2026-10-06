#!/bin/bash
# Pause (SIGSTOP) only the processes this experiment started while the 1-min load average is >= 300; resume (SIGCONT) below 280.
state=run
mine() { for p in $(pgrep -f "cpu_ocr.py --batch|vision_json.py fixtures|cached_ocr.py|run_check.py"); do echo $p; pgrep -P $p; done; }
while [ -e /Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment/governor.on ]; do
  l=$(sysctl -n vm.loadavg | awk '{print int($2)}')
  if [ $l -ge 300 ] && [ $state = run ]; then state=stop; for p in $(mine); do kill -STOP $p 2>/dev/null; done; echo "$(date +%T) load $l: paused" >> logs/governor.log; fi
  if [ $state = stop ]; then for p in $(mine); do kill -STOP $p 2>/dev/null; done; fi   # catch children started meanwhile
  if [ $l -lt 280 ] && [ $state = stop ]; then state=run; for p in $(mine); do kill -CONT $p 2>/dev/null; done; echo "$(date +%T) load $l: resumed" >> logs/governor.log; fi
  sleep 15
done
