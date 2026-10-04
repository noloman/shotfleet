#!/bin/zsh
setopt SH_WORD_SPLIT NULL_GLOB
# Experiment A. Needs the device lock. Own emulator (read-only copy of shotfleet_android, port 5760). Maestro 2.11.0 from scratch, own user.home.
S=<scratch>; A=$S/expA; SDK=$HOME/Library/Android/sdk; PORT=5760; DEV=emulator-$PORT; ADB="$SDK/platform-tools/adb -s $DEV"
export JAVA_OPTS="-Duser.home=$S/homeA" MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_DISABLE_UPDATE_CHECK=true
M=$S/maestro211/maestro/bin/maestro
cd $A; rm -rf debug-* shots-* run-*.log
if ! adb devices | grep -q "$DEV"; then $SDK/emulator/emulator -avd shotfleet_android -port $PORT -no-window -no-audio -no-boot-anim -snapshot shotfleet -no-snapshot-save -read-only > emu.log 2>&1  & EMU=$!; echo $EMU > emu.pid; else EMU=$(cat emu.pid); fi
for i in $(seq 1 120); do [ "$($ADB shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && break; sleep 3; done
echo "booted after ~$((i*3)) s; $($ADB shell getprop ro.build.version.release | tr -d '\r') $($ADB shell getprop ro.product.cpu.abi | tr -d '\r')"
$ADB install -r -g $S/apk/FleetFixture.apk | tail -1
$ADB shell cmd locale set-app-locales com.shotfleet.fixture --locales ja
$ADB shell cmd locale get-app-locales com.shotfleet.fixture
# run 1: control, markers only
t0=$(date +%s); $M --device $DEV test --shard-all 1 --debug-output debug-control flow-control.yaml > run-control.log 2>&1; echo "control rc=$? secs=$(($(date +%s)-t0))" | tee -a run-control.log
# run 2: probe: 'maestro hierarchy' while the sharded run sits in its 40 s wait step
$ADB shell cmd locale set-app-locales com.shotfleet.fixture --locales ja
t0=$(date +%s); $M --device $DEV test --shard-all 1 --debug-output debug-probe flow-probe.yaml > run-probe.log 2>&1 &
RUN=$!
for i in $(seq 1 60); do grep -q "probe-window" run-probe.log && break; sleep 1; done
sleep 3; echo "probe start at $(($(date +%s)-t0)) s into the run"
( $M --device $DEV hierarchy > probe-hierarchy.out 2> probe-hierarchy.err; echo "hierarchy rc=$?" > probe-hierarchy.rc ) &
PROBE=$!
sleep 25; kill -0 $PROBE 2>/dev/null && { echo "hierarchy probe STILL RUNNING after 25 s: killing pid $PROBE"; kill $PROBE; echo "killed" >> probe-hierarchy.rc; }
wait $RUN; echo "probe-run rc=$? secs=$(($(date +%s)-t0))" | tee -a run-probe.log
$ADB emu kill >/dev/null 2>&1; sleep 5; kill -0 $EMU 2>/dev/null && kill $EMU
echo finished
