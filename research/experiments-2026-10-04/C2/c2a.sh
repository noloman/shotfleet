#!/bin/zsh
setopt SH_WORD_SPLIT
R=<scratch>; REPO=~/Developer/shotfleet/.claude/worktrees/clever-lehmann-328f4b
export JAVA_OPTS="-Duser.home=$R/home-c2" MAESTRO_CLI_NO_ANALYTICS=1
cd $REPO; SF="python3 $REPO/shotfleet.py"
rm -rf $R/c2android/out
t0=$(date +%s); $SF run $R/c2android/shotfleet.toml --platform android --locales de,ja --parallel 1 > $R/c2android/run.log 2>&1; echo "android run rc=$? secs=$(($(date +%s)-t0))" | tee -a $R/c2android/run.log
$SF check $R/c2android/out > $R/c2android/check.log 2>&1; echo "check rc=$?" | tee -a $R/c2android/check.log
echo finished-android
