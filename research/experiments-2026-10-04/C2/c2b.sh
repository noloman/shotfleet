#!/bin/zsh
setopt SH_WORD_SPLIT
R=<scratch>; REPO=~/Developer/shotfleet/.claude/worktrees/clever-lehmann-328f4b
export JAVA_OPTS="-Duser.home=$R/home-c2" MAESTRO_CLI_NO_ANALYTICS=1
cd $REPO; SF="python3 $REPO/shotfleet.py"
rm -rf $R/c2ios5/out
if false; then :; else
  t0=$(date +%s); $SF run $R/c2ios5/shotfleet.toml --parallel 2 > $R/c2ios5/run.log 2>&1; echo "ios5 run rc=$? secs=$(($(date +%s)-t0))" | tee -a $R/c2ios5/run.log
  $SF check $R/c2ios5/out > $R/c2ios5/check.log 2>&1; echo "check rc=$?" | tee -a $R/c2ios5/check.log
fi
[ -f $R/c2ios5/check.log ] && grep -q "^check rc=0" $R/c2ios5/check.log && touch $R/c2b.done
echo finished-ios5
