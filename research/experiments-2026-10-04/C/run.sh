#!/bin/zsh
# Experiment C. Needs the device lock. shotfleet boots/removes its own shotfleet-<device>-N simulators; Maestro 2.0.10 (shotfleet's tested default) with its Java home in scratch.
S=<scratch>; cd ~/Developer/shotfleet/.claude/worktrees/clever-lehmann-328f4b
export JAVA_OPTS="-Duser.home=$S/homeC" MAESTRO_CLI_NO_ANALYTICS=1
rm -rf $S/expC/out
t0=$(date +%s); python3 shotfleet.py run $S/expC/shotfleet.toml --locales de,ja --parallel 1 > $S/expC/run.log 2>&1; echo "run rc=$? secs=$(($(date +%s)-t0))" | tee -a $S/expC/run.log
python3 shotfleet.py check $S/expC/out > $S/expC/check.log 2>&1; echo "check rc=$?" | tee -a $S/expC/check.log
