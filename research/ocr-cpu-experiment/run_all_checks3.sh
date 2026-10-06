#!/bin/bash
cd /Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment
export CPU_OCR_CACHE=$PWD/cache; APK=$PWD/fixtures/android/app.apk
for k in cpu tess6; do
  if [ $k = cpu ]; then C="$PWD/venv/bin/python $PWD/cached_ocr.py {image} {lang}"; P=/usr/bin:/bin; else C="tesseract {image} stdout -l {tesseract} --psm 6"; P=/opt/homebrew/bin:/usr/bin:/bin; fi
  echo "$(date +%T) ${k}_android_sens start load $(sysctl -n vm.loadavg)"
  /usr/bin/time -l env NO_OSD=1 PATH=$P nice -n 10 perl -e 'alarm 1500; exec @ARGV' $PWD/venv/bin/python run_check.py cmd fixtures/android/sens $APK report_${k}_android_sens "$C" > logs/check_${k}_android_sens.log 2>&1
  echo "$(date +%T) ${k}_android_sens done"
done
