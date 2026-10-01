#!/bin/sh
# usage: run.sh <avd> <port> <label> [extra emulator flags]
AVD=$1; P=$2; L=$3; shift 3
E=~/Library/Android/sdk/emulator/emulator
$E -avd $AVD -port $P -no-window -no-audio -no-boot-anim -no-snapshot "$@" >/tmp/emu_$P.log 2>&1 &
S=emulator-$P
adb -s $S wait-for-device
until [ "$(adb -s $S shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ]; do sleep 2; done
sleep 120
PID=$(pgrep -f "qemu.*-port $P" | head -1)
[ -z "$PID" ] && PID=$(pgrep -f "port $P" | head -1)
FP=$(footprint -p $PID 2>/dev/null | awk '/phys_footprint:/{print $2,$3; exit}')
RSS=$(ps -o rss= -p $PID)
PROCS=$(adb -s $S shell ps -A | wc -l | tr -d ' ')
USED=$(adb -s $S shell cat /proc/meminfo | awk '/MemTotal/{t=$2}/MemAvailable/{a=$2}END{print int((t-a)/1024)"MB"}')
echo "$L pid=$PID footprint=$FP rss=$((RSS/1024))MB guest_procs=$PROCS guest_used=$USED"
