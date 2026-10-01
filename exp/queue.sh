#!/bin/sh
# reruns for runs lost to emulator startup crashes; waits for campaign pid $1
while kill -0 "$1" 2>/dev/null; do sleep 20; done
sleep 60; python3 exp/fleet.py droidslim_test 10 n10_slim_r2b || echo "RUN FAILED n10_slim_r2b"
sleep 60; python3 exp/fleet.py droidslim_stock 10 n10_stock_r3b || echo "RUN FAILED n10_stock_r3b"
