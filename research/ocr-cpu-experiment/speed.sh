#!/bin/bash
# Speed and peak memory per full-size screenshot: a fresh process per image (model load included), /usr/bin/time -l gives wall, CPU seconds and peak RSS.
# usage: speed.sh  (writes logs/speed.tsv: variant, image, load-before, wall, user+sys CPU s, peak RSS MB)
cd /Users/manu/Developer/shotfleet-rc-build/ocr-cpu-experiment
S=fixtures/base
IMGS="$S/de-DE/iphone-69-02-fit-trust.png:de-DE $S/ja/iphone-69-05-weekly-briefing.png:ja $S/ru/ipad-13-03-saved-and-tracker.png:ru"
one() { # variant env... ; image:lang
  local v=$1 img=${2%%:*} lang=${2##*:}; shift 2
  local l=$(sysctl -n vm.loadavg | awk '{print $2}')
  /usr/bin/time -l env "$@" nice -n 10 perl -e 'alarm 600; exec @ARGV' venv/bin/python cpu_ocr.py $img $lang > /dev/null 2> logs/speed.tmp
  awk -v v="$v" -v i="$(basename $img)" -v l="$l" '/ real/{w=$1} / user/{u=$1} / sys/{s=$1} /maximum resident/{r=$1/1048576} END{printf "%s\t%s\tload %s\twall %.1f s\tcpu %.1f s\tRSS %.0f MB\n", v,i,l,w,u+s,r}' logs/speed.tmp | tee -a logs/speed.tsv
}
for im in $IMGS; do
  one "1 thread, side 2000" $im CPU_OCR_THREADS=1 CPU_OCR_MAXSIDE=2000
  one "4 threads, side 2000" $im CPU_OCR_THREADS=4 CPU_OCR_MAXSIDE=2000
  one "10 threads, side 2000" $im CPU_OCR_THREADS=10 CPU_OCR_MAXSIDE=2000
  one "1 thread, side 1600" $im CPU_OCR_THREADS=1 CPU_OCR_MAXSIDE=1600
  one "1 thread, side 1200" $im CPU_OCR_THREADS=1 CPU_OCR_MAXSIDE=1200
  one "1 thread, v6 small (latin only)" $im CPU_OCR_THREADS=1 CPU_OCR_V6=1
done
