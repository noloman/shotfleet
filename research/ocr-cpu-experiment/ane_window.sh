#!/bin/bash
# ANE service CPU seconds consumed per wall second over a window: ane_window.sh <label> <seconds>   (ps cputime has 10 ms resolution)
secs() { ps -o time= -p $1 | awk -F'[:]' '{ if (NF==3) print $1*3600+$2*60+$3; else print $1*60+$2 }'; }
p=$(pgrep -f ANECompilerService | head -1); a=$(secs $p); sleep $2; b=$(secs $p)
echo "$1 $(date +%T) load $(sysctl -n vm.loadavg | awk '{print $2}') ANE cpu +$(echo "$b - $a" | bc) s in $2 s"
