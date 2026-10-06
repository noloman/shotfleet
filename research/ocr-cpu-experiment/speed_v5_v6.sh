#!/bin/bash
# v5 latin vs v6 small on the same three Latin screenshots, one thread, fresh process each, two repeats (writes logs/speed_v5_v6.tsv)
cd /Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment
for img in fixtures/base/de-DE/iphone-69-02-fit-trust.png:de-DE fixtures/base/ro/iphone-69-05-weekly-briefing.png:ro fixtures/base/nl-NL/ipad-13-03-saved-and-tracker.png:nl-NL; do
 for rep in 1 2; do for v in 5 6; do
  l=$(sysctl -n vm.loadavg | awk '{print $2}')
  /usr/bin/time -l env CPU_OCR_THREADS=1 CPU_OCR_V6=$([ $v = 6 ] && echo 1 || echo 0) nice -n 10 venv/bin/python cpu_ocr.py ${img%%:*} ${img##*:} > /dev/null 2> logs/speed.tmp
  awk -v v="v$v" -v i="$(basename ${img%%:*})" -v l="$l" '/ real/{w=$1} / user/{u=$1} / sys/{s=$1} /maximum resident/{r=$1/1048576} END{printf "%s\t%s\tload %s\twall %.1f s\tcpu %.1f s\tRSS %.0f MB\n", v,i,l,w,u+s,r}' logs/speed.tmp | tee -a logs/speed_v5_v6.tsv
 done; done; done
