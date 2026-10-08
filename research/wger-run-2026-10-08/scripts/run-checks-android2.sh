#!/bin/bash
S=/Users/manu/Developer/shotfleet-rc-build/showcase-wger; SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
export ANDROID_HOME=/Users/manu/Library/Android/sdk
cd $S
for r in android-dry android-run1 android-run2; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') check $r (--strings only, as the iPhone job; --app APK exits 1 for Flutter) started" >> progress.log
  perl -e 'alarm 1200; exec @ARGV' $SF check out-$r --strings "$S/src/lib/l10n/*.arb" --report check-$r > logs/check-$r.log 2>&1; echo "rc=$?" >> logs/check-$r.log
  echo "$(date '+%Y-%m-%d %H:%M:%S') check $r done: $(tail -3 logs/check-$r.log | tr '\n' ' ')" >> progress.log
done
echo "$(date '+%Y-%m-%d %H:%M:%S') all android checks (strings-only) done" >> progress.log
