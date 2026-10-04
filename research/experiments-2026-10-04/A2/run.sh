#!/bin/zsh
# R2a. Needs the device lock. Two read-only copies of shotfleet_android on ports 5760/5762 (own), two shards in parallel.
# usage: run.sh <label> <maestro-bin> <locale> <tap-text> <markers 0|1> <probe 0|1>
setopt SH_WORD_SPLIT NULL_GLOB
L=$1; M=$2; LOC=$3; TAP=$4; MARK=$5; PROBE=$6
R=<scratch>
SDK=$HOME/Library/Android/sdk; A=$R/a2; HOMEDIR=$R/home-$L
export JAVA_OPTS="-Duser.home=$HOMEDIR" MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_DISABLE_UPDATE_CHECK=true
cd $A; rm -rf flows-$L debug-$L shots-$L-* $L.log; mkdir flows-$L
for n in 1 2; do
  { printf 'appId: com.shotfleet.fixture\nname: a2-%s-%s\n---\n- launchApp\n- takeScreenshot: shots-%s-%s/01_welcome\n' $L $n $L $n
    [ $MARK = 1 ] && printf -- '- assertTrue:\n    condition: ${false}\n    label: "shotfleet:hier:01_welcome"\n    optional: true\n'
    [ $PROBE = 1 ] && printf -- '- extendedWaitUntil:\n    visible: "zzzz-never-visible"\n    timeout: 40000\n    optional: true\n    label: "probe-window"\n'
    printf -- '- tapOn: "%s"\n- takeScreenshot: shots-%s-%s/02_settings\n' $TAP $L $n
    [ $MARK = 1 ] && printf -- '- assertTrue:\n    condition: ${false}\n    label: "shotfleet:hier:02_settings"\n    optional: true\n'
  } > flows-$L/flow-$n.yaml
done
for P in 5760 5762; do
  if ! adb devices | grep -q "emulator-$P"; then $SDK/emulator/emulator -avd shotfleet_android -port $P -no-window -no-audio -no-boot-anim -snapshot shotfleet -no-snapshot-save -read-only > emu-$P.log 2>&1 & echo $! >> emu.pids; fi
done
for P in 5760 5762; do
  for i in $(seq 1 120); do [ "$(adb -s emulator-$P shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && break; sleep 3; done
  echo "emulator-$P booted after ~$((i*3)) s"
  adb -s emulator-$P install -r -g $R/apk/FleetFixture.apk | tail -1
  adb -s emulator-$P shell cmd locale set-app-locales com.shotfleet.fixture --locales $LOC
  adb -s emulator-$P shell cmd locale get-app-locales com.shotfleet.fixture
done
t0=$(date +%s)
$M --device emulator-5760,emulator-5762 test --shard-split 2 --debug-output debug-$L flows-$L > $L.log 2>&1 &
RUN=$!; echo "run pid $RUN"
if [ $PROBE = 1 ]; then
  sleep 30
  sleep 3; echo "probe start at $(( $(date +%s)-t0 )) s into the run; shards running: $(pgrep -f "maestro.cli.*debug-$L" | wc -l)"
  for P in 5760 5762; do
    ( $M --device emulator-$P hierarchy > probe-$L-$P.out 2> probe-$L-$P.err; echo "rc=$?" > probe-$L-$P.rc ) & echo $! > probe-$L-$P.pid
  done
  sleep 30
  for P in 5760 5762; do pid=$(cat probe-$L-$P.pid); if kill -0 $pid 2>/dev/null; then echo "probe $P STILL RUNNING after 30 s: killing exact pid $pid"; kill $pid; echo killed >> probe-$L-$P.rc; fi; done
fi
for i in $(seq 1 100); do kill -0 $RUN 2>/dev/null || break; sleep 3; done
if kill -0 $RUN 2>/dev/null; then echo "RUN HUNG: still running after $(( $(date +%s)-t0 )) s; killing exact pid $RUN"; kill $RUN; echo HUNG > hung-$L.flag; else wait $RUN; echo "$L rc=$? secs=$(( $(date +%s)-t0 ))"; fi
for P in 5760 5762; do adb -s emulator-$P emu kill >/dev/null 2>&1; done; sleep 8
for pid in $(cat emu.pids 2>/dev/null); do kill -0 $pid 2>/dev/null && kill $pid; done; rm -f emu.pids
echo finished-$L
