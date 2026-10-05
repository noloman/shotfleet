#!/bin/zsh
# Experiment B. Needs the device lock. Creates ONE new simulator (expB-capdemo), deletes only that one at the end.
S=<scratch>; B=$S/expB; APP=$S/capapp/build/Build/Products/Debug-iphonesimulator/App.app; ID=dev.shotfleet.capdemo
export JAVA_OPTS="-Duser.home=$S/homeA" MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_DISABLE_UPDATE_CHECK=true
M=$S/maestro211/maestro/bin/maestro
cd $B; rm -f *.png *.txt
RT=$(xcrun simctl list runtimes -j | python3 -c "import json,sys; r=[x for x in json.load(sys.stdin)['runtimes'] if x['platform']=='iOS' and x['isAvailable']]; print(sorted(r,key=lambda x:x['version'])[-1]['identifier'])")
UDID=$(xcrun simctl create expB-capdemo com.apple.CoreSimulator.SimDeviceType.iPhone-17-Pro $RT); echo "runtime=$RT udid=$UDID" | tee info.txt
xcrun simctl bootstatus $UDID -b >/dev/null 2>&1; xcrun simctl install $UDID $APP
shot() { # $1=label; screenshot plus the hierarchy text
  sleep 6; xcrun simctl io $UDID screenshot $B/$1.png >/dev/null 2>&1
  $M --device $UDID hierarchy 2>/dev/null | python3 -c "
import json,sys,re
t=sys.stdin.read(); i=t.find('{')
d=json.loads(t[i:]) if i>=0 else {}
out=[]
def w(n):
    if isinstance(n,dict):
        a=n.get('attributes',{})
        for k in ('text','accessibilityText','value','title'):
            v=a.get(k)
            if v and v not in out: out.append(v)
        for c in n.get('children',[]): w(c)
w(d); print('\n'.join(out))" > $B/$1.txt
  echo "== $1: $(grep -E 'navigator|Hello|Hallo|device=' $B/$1.txt | tr '\n' '|')" | tee -a info.txt
}
xcrun simctl launch --terminate-running-process $UDID $ID > /dev/null;                                 shot 1-default-en
xcrun simctl launch --terminate-running-process $UDID $ID -AppleLanguages "(de)" -AppleLocale de_DE >/dev/null; shot 2-arg-de
xcrun simctl launch --terminate-running-process $UDID $ID -AppleLanguages "(ja)" -AppleLocale ja_JP >/dev/null; shot 3-arg-ja
# positive control: the SYSTEM language set to German on this throwaway simulator, then reboot
xcrun simctl shutdown $UDID; xcrun simctl spawn $UDID defaults write -g AppleLanguages '(de)' 2>/dev/null || true
xcrun simctl boot $UDID; xcrun simctl bootstatus $UDID -b >/dev/null 2>&1
xcrun simctl spawn $UDID defaults write -g AppleLanguages '(de)'; xcrun simctl spawn $UDID defaults write -g AppleLocale de_DE
xcrun simctl shutdown $UDID; xcrun simctl boot $UDID; xcrun simctl bootstatus $UDID -b >/dev/null 2>&1
xcrun simctl launch --terminate-running-process $UDID $ID > /dev/null;                                 shot 4-system-de
xcrun simctl shutdown $UDID; xcrun simctl delete $UDID; echo "deleted $UDID" | tee -a info.txt
