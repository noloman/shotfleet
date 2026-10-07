#!/bin/bash
S=/Users/manu/Developer/shotfleet-rc-build/showcase-wod; SF=/Users/manu/Developer/shotfleet-rc-build/0.1.6/unpacked/shotfleet/shotfleet
cd $S
for r in iphone-run1 iphone-run2 iphone-run3 iphone-dry; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') check $r started" >> progress.log
  perl -e 'alarm 1200; exec @ARGV' $SF check out-$r --app "$S/app/Crossfit Tracker.app" --report check-$r > logs/check-$r.log 2>&1; echo "rc=$?" >> logs/check-$r.log
  echo "$(date '+%Y-%m-%d %H:%M:%S') check $r done: $(tail -3 logs/check-$r.log | tr '\n' ' ')" >> progress.log
done
echo "$(date '+%Y-%m-%d %H:%M:%S') all checks done" >> progress.log
