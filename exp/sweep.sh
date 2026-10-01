#!/bin/sh
# fleet-size sweep, 3 variants; variant order reverses on rep 2 to counterbalance drift.
calm() { # up to 5 min for host memory pressure to return to normal between runs
  i=0; while [ "$(sysctl -n kern.memorystatus_vm_pressure_level)" != 1 ] && [ $i -lt 15 ]; do sleep 20; i=$((i+1)); done; sleep 30; }
run() { case $2 in stock) avd=droidslim_stock;; slim) avd=droidslim_test;; atd) avd=droidslim_atd;; esac
  calm; python3 exp/fleet.py $avd $1 app_n$1_$2_r$3 || echo "RUN FAILED app_n$1_$2_r$3"; }
for n in 8 6 4; do run $n stock 1; run $n slim 1; run $n atd 1; done
for n in 8 6 4; do run $n atd 2; run $n slim 2; run $n stock 2; done
