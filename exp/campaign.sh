#!/bin/sh
# interleaved so any drift in host state hits both variants equally
for r in 1 2 3; do
  for v in stock slim; do
    [ $v = stock ] && avd=droidslim_stock || avd=droidslim_test
    sleep 60
    python3 exp/fleet.py $avd 10 n10_${v}_r$r || echo "RUN FAILED n10_${v}_r$r"
  done
done
