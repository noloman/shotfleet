#!/bin/zsh
# R2b. Needs the device lock. Part 1: one NEW iOS 18.6 simulator (expB2-ios18, deleted at the end). Part 2: one read-only shotfleet_android emulator on port 5760 (own).
setopt SH_WORD_SPLIT NULL_GLOB
R=<scratch>
B=$R/b2; APP=$R/capapp/build/Build/Products/Debug-iphonesimulator/App.app; APK=$R/capapp/android/app/build/outputs/apk/debug/app-debug.apk; ID=dev.shotfleet.capdemo
export JAVA_OPTS="-Duser.home=$R/home-b2" MAESTRO_CLI_NO_ANALYTICS=1 MAESTRO_DISABLE_UPDATE_CHECK=true
M=$R/maestro211/maestro/bin/maestro; SDK=$HOME/Library/Android/sdk
cd $B; rm -f *.png *.txt
dump() { python3 -c "
import json,sys
t=sys.stdin.read(); i=t.find('{'); d=json.loads(t[i:]) if i>=0 else {}
out=[]
def w(n):
    if isinstance(n,dict):
        a=n.get('attributes',{})
        for k in ('text','accessibilityText','value','title','content-desc'):
            v=a.get(k)
            if v and v not in out: out.append(v)
        for c in n.get('children',[]): w(c)
w(d); print('\n'.join(out))"; }
UDID=$(xcrun simctl create expB2-ios18 com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro com.apple.CoreSimulator.SimRuntime.iOS-18-6); echo "ios18 udid=$UDID" | tee info.txt
xcrun simctl bootstatus $UDID -b >/dev/null 2>&1; xcrun simctl install $UDID $APP
ishot() { sleep 6; xcrun simctl io $UDID screenshot $B/$1.png >/dev/null 2>&1; $M --device $UDID hierarchy 2>/dev/null | dump > $B/$1.txt; echo "== $1: $(grep -E 'navigator|Hello|Hallo|device=' $B/$1.txt | tr '\n' '|')" | tee -a info.txt; }
xcrun simctl launch --terminate-running-process $UDID $ID >/dev/null;                                           ishot ios18-1-default
xcrun simctl launch --terminate-running-process $UDID $ID -AppleLanguages "(de)" >/dev/null;                     ishot ios18-2-argonly-de
xcrun simctl launch --terminate-running-process $UDID $ID -AppleLanguages "(ja)" >/dev/null;                     ishot ios18-3-argonly-ja
xcrun simctl launch --terminate-running-process $UDID $ID -AppleLanguages "(de)" -AppleLocale de_DE >/dev/null;  ishot ios18-4-arg-and-locale-de
xcrun simctl shutdown $UDID; xcrun simctl spawn $UDID defaults write -g AppleLanguages '(de)' 2>/dev/null
xcrun simctl boot $UDID; xcrun simctl bootstatus $UDID -b >/dev/null 2>&1
xcrun simctl spawn $UDID defaults write -g AppleLanguages '(de)'; xcrun simctl spawn $UDID defaults write -g AppleLocale de_DE
xcrun simctl shutdown $UDID; xcrun simctl boot $UDID; xcrun simctl bootstatus $UDID -b >/dev/null 2>&1
xcrun simctl launch --terminate-running-process $UDID $ID >/dev/null;                                           ishot ios18-5-system-de
xcrun simctl shutdown $UDID; xcrun simctl delete $UDID; echo "deleted $UDID" | tee -a info.txt
P=5760; E=emulator-$P; AD="$SDK/platform-tools/adb -s $E"
if ! adb devices | grep -q $E; then $SDK/emulator/emulator -avd shotfleet_android -port $P -no-window -no-audio -no-boot-anim -snapshot shotfleet -no-snapshot-save -read-only > emu.log 2>&1 & echo $! > emu.pid; fi
for i in $(seq 1 120); do [ "$($AD shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" = 1 ] && break; sleep 3; done
echo "android emulator booted after ~$((i*3)) s; release $($AD shell getprop ro.build.version.release | tr -d '\r'); webview $($AD shell dumpsys webviewupdate 2>/dev/null | grep -m1 'Current WebView package' | tr -d '\r')" | tee -a info.txt
$AD install -r $APK | tail -1
ashot() { sleep 6; $AD exec-out screencap -p > $B/$1.png; $M --device $E hierarchy 2>/dev/null | dump > $B/$1.txt; echo "== $1: $(grep -E 'navigator|Hello|Hallo|device=' $B/$1.txt | tr '\n' '|')" | tee -a info.txt; }
$AD shell cmd locale set-app-locales $ID --locales en-US; $AD shell am force-stop $ID; $AD shell am start -n $ID/.MainActivity >/dev/null; ashot android-1-default
$AD shell cmd locale set-app-locales $ID --locales de;      $AD shell am force-stop $ID; $AD shell am start -n $ID/.MainActivity >/dev/null; ashot android-2-applocale-de
$AD shell cmd locale set-app-locales $ID --locales ja;      $AD shell am force-stop $ID; $AD shell am start -n $ID/.MainActivity >/dev/null; ashot android-3-applocale-ja
$AD shell cmd locale set-app-locales $ID --locales ""
$AD emu kill >/dev/null 2>&1; sleep 8; [ -f emu.pid ] && { kill -0 $(cat emu.pid) 2>/dev/null && kill $(cat emu.pid); rm -f emu.pid; }
echo finished | tee -a info.txt
