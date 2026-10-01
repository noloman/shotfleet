#!/bin/sh
# ATD vs ATD+slim at 8 emulators, 2 reps, order alternates to counterbalance drift
calm() { i=0; while [ "$(sysctl -n kern.memorystatus_vm_pressure_level)" != 1 ] && [ $i -lt 15 ]; do sleep 20; i=$((i+1)); done; sleep 30; }
run() { calm; python3 exp/fleet.py $1 8 $2 --settle 60 --load 180 || echo "RUN FAILED $2"; }
run droidslim_atd     focus_n8_atd_r1
run droidslim_atdslim focus_n8_atdslim_r1
run droidslim_atdslim focus_n8_atdslim_r2
run droidslim_atd     focus_n8_atd_r2
