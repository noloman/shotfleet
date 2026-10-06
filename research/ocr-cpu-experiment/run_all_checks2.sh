#!/bin/bash
# second round: Android/Arabic arm (CPU v5 + Tesseract) and the PP-OCRv6 Latin variant on the iOS folders
cd /Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment
export CPU_OCR_CACHE=$PWD/cache
IOS=/Users/manu/Developer/shotfleet-rc-build/c030-retime/ios/remoti.app; APK=$PWD/fixtures/android/app.apk
CPU="$PWD/venv/bin/python $PWD/cached_ocr.py {image} {lang}"; TESS="tesseract {image} stdout -l {tesseract} --psm 6"
run() { # name folder app path cmd [extra env]
  echo "$(date +%T) $1 start load $(sysctl -n vm.loadavg)"
  /usr/bin/time -l env NO_OSD=1 $6 PATH=$4 nice -n 10 perl -e 'alarm 1500; exec @ARGV' $PWD/venv/bin/python run_check.py cmd $2 $3 report_$1 "$5" > logs/check_$1.log 2>&1
  echo "$(date +%T) $1 done"
}
run cpu_android_clean fixtures/android/clean $APK /usr/bin:/bin "$CPU"
run cpu_android_planted fixtures/android/planted $APK /usr/bin:/bin "$CPU"
run tess6_android_clean fixtures/android/clean $APK /opt/homebrew/bin:/usr/bin:/bin "$TESS"
run tess6_android_planted fixtures/android/planted $APK /opt/homebrew/bin:/usr/bin:/bin "$TESS"
run cpu_v6_base fixtures/base $IOS /usr/bin:/bin "$CPU" CPU_OCR_V6=1
run cpu_v6_sens fixtures/sens $IOS /usr/bin:/bin "$CPU" CPU_OCR_V6=1
