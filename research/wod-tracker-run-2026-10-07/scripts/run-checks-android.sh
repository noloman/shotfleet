#!/bin/bash
S=/Users/manu/Developer/shotfleet-rc-build/showcase-wod; SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
export ANDROID_HOME=/Users/manu/Library/Android/sdk
cd $S
for r in android-run1 android-run2 android-dry android-zhsmoke; do
  [ -d out-$r ] || continue
  echo "$(date '+%Y-%m-%d %H:%M:%S') check $r started" >> progress.log
  perl -e 'alarm 1200; exec @ARGV' $SF check out-$r --app "$S/app/androidApp-debug.apk" --report check-$r > logs/check-$r.log 2>&1; echo "rc=$?" >> logs/check-$r.log
  echo "$(date '+%Y-%m-%d %H:%M:%S') check $r done: $(tail -3 logs/check-$r.log | tr '\n' ' ')" >> progress.log
done
echo "$(date '+%Y-%m-%d %H:%M:%S') all android checks done" >> progress.log
