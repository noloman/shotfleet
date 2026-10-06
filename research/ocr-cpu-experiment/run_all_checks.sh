#!/bin/bash
# check runs of the CPU reader and Tesseract on base and sens folders (cache seeded from the batch run; misses are read for real)
cd /Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment
APP=/Users/manu/Developer/shotfleet-rc-build/c030-retime/ios/remoti.app
export CPU_OCR_CACHE=$PWD/cache
run() { # name folder noosd path cmd
  echo "$(date +%T) $1 start load $(sysctl -n vm.loadavg)"
  /usr/bin/time -l env NO_OSD=$3 PATH=$4 nice -n 10 perl -e 'alarm 1500; exec @ARGV' $PWD/venv/bin/python run_check.py cmd $2 $APP report_$1 "$5" > logs/check_$1.log 2>&1
  echo "$(date +%T) $1 done"
}
CPU="$PWD/venv/bin/python $PWD/cached_ocr.py {image} {lang}"
run cpu_sens fixtures/sens 1 /usr/bin:/bin "$CPU"
run tess6_base fixtures/base 1 /opt/homebrew/bin:/usr/bin:/bin "tesseract {image} stdout -l {tesseract} --psm 6"
run tess6_sens fixtures/sens 1 /opt/homebrew/bin:/usr/bin:/bin "tesseract {image} stdout -l {tesseract} --psm 6"
run cpu_base_osd fixtures/base 0 /opt/homebrew/bin:/usr/bin:/bin "$CPU"
run cpu_sens_osd fixtures/sens 0 /opt/homebrew/bin:/usr/bin:/bin "$CPU"
