# Why `KeysiNotary` "disappears" (2026-10-06)

Read-only investigation on Manu's Mac (macOS 27.0 26A428, Xcode 27.0, notarytool 1.1.3). No keychain item was read for its secret, changed, exported or deleted. Every claim is marked **MEASURED** (seen on this Mac today, command given) or **INFERENCE**.

## Answer

The profile was not deleted. **It was locked.** notarytool keeps the profile in the data protection keychain, in an item that can only be read while the Mac is unlocked. When the screen locks, the keybag locks five minutes later. After that every `notarytool --keychain-profile` call fails, and notarytool reports the failure as `Error: No Keychain password item found for profile: KeysiNotary`. That is the same text it prints for a profile that really is missing. Unlocking the Mac "restores" the profile without anyone storing it again.

Sharing the profile with Keysi did not cause the 2026-10-05/06 failure: in the whole window no process wrote, updated or deleted the item. A separate `ShotfleetNotary` profile is still worth having (see Prevention), but on its own it fails the same way the first time the screen locks during a release.

## Evidence

### Where the profile lives

- **MEASURED.** It is not in the file-based login keychain. `security find-generic-password -l KeysiNotary`, `-a com.apple.gke.notary.tool.saved-creds.KeysiNotary` and `-s ...` all return "could not be found", and `security dump-keychain | grep -i -E 'notary|gke'` (attributes only, no `-d`) finds nothing. This is true now, while the profile works.
- **MEASURED.** notarytool is signed with `keychain-access-groups = [com.apple.gke.notary]` (`codesign -d --entitlements - $(xcrun -f notarytool)`). In the unified log its lookups are `SecItemCopyMatching_ios`, which is the data protection keychain path, and they are answered by `secd`, not by the file-keychain `securityd`. The item is stored under `~/Library/Keychains/3F190864-.../keychain-2.db`.
- **INFERENCE (from the above).** The `security` CLI cannot list data protection keychain items. So "`security find-generic-password` finds no notarytool item" proves nothing: it returns that answer even when the profile works. Keysi's `RELEASE.md` (lines 140-146, the 2026-09-11 incident) took that check as proof the item was gone, and it reasoned "the login keychain is `no-timeout`, so this was not a lock". The login keychain's timeout does not apply here, because the item is not in the login keychain.
- **INFERENCE.** For the same reason, changing the keychain search list (`list-keychains -s`, `default-keychain`, temporary build keychains) cannot hide this item. The search list only covers file keychains.
- **iCloud sync.** None of our docs use `store-credentials --sync`, so the item should be local-only (INFERENCE). Its attributes cannot be read from a shell. Sync deletion is ruled out by the next section anyway: the item was still there after unlock without being stored again.

### What happened between 2026-10-05 18:49 and 2026-10-06 ~00:58

Source: `/usr/bin/log show --start '2026-10-05 17:00' --end '2026-10-06 09:00' --info --debug --predicate 'process == "notarytool" OR eventMessage CONTAINS[c] "gke.notary" OR ...'`, plus loginwindow and coreauthd keybag events over the same window. All MEASURED.

| Time (CEST) | Event |
|---|---|
| 18:48-18:49 | notarytool submissions succeed (shotfleet 0.1.3). |
| 20:24:55 | Screen locks. |
| 20:29:54 → 20:30:04 | Keybag `Locking` → `Locked` (5 min after the screen lock). |
| 20:30:27-20:30:36 | 3 notarytool runs. `secd`: `copy_matching ... Code=-25308 "Access to item attempted while keychain is locked" (class 6 ...)`. |
| 20:40:50 | Screen and keybag unlocked. |
| 20:42-20:47 | notarytool runs succeed with the same profile, which nobody stored again. |
| 00:01-00:07 | notarytool runs succeed (Mac unlocked). |
| 00:10:11 | Screen locks. |
| 00:15:20 | Keybag `Locked`. |
| 00:50-02:20 | notarytool runs about every 5 minutes, and every one gets `-25308` (22 failures). In a Keysi session, notarytool printed this at that time as `No Keychain password item found for profile: KeysiNotary` (session "Full-scale code review", found by transcript search). |
| 08:14:49 | Mac unlocked. |
| 08:20-08:22 | notarytool lookups succeed. |

- **MEASURED.** In the window, `secd` logged 25 errors for notarytool, all `-25308` (errSecInteractionNotAllowed: locked). It logged none with `-25300` (item not found).
- **MEASURED.** In the window, notarytool made 63 keychain calls, all `SecItemCopyMatching`. There was no `SecItemAdd`, `SecItemUpdate` or `SecItemDelete`, so no `store-credentials` and no delete ran between 2026-10-05 17:00 and 2026-10-06 08:35. If the owner stored the profile again this morning, it was after 08:35. Before that, the unlock at 08:14 had already made it work.
- **MEASURED.** Every failure fell inside a keybag-`Locked` period, and every success fell outside one.
- **MEASURED.** There was no reboot since 2026-10-02 08:32 (`sysctl kern.boottime`), so no OS update or restart took place in the window. Display sleep is 10 min (`pmset -g`), the screensaver starts at 1200 s, and the login keychain is `no-timeout` (`security show-keychain-info`; that setting does not apply to this item).

### The earlier incidents

- **2026-09-11 (Keysi).** The profile worked at 17:28 and failed at 17:35. **INFERENCE:** the gap fits screen lock plus the 5-minute keybag grace. The logs from that day are no longer kept, so this cannot be checked.
- **~2026-10-03/04 (shotfleet, the one in `limits-release-engineering-2026-10-05.md` section 3).** The unified log on this Mac still covers 2026-10-01 onward. It has no `secd` errors for notarytool between 2026-10-03 and 2026-10-05 12:00. The detailed `SecItem*` activity lines for those days have already rotated out, so whether that failure was a lock cannot be measured. **MEASURED from session transcripts:** shotfleet sessions on 2026-10-04 and 2026-10-05 ran notarytool with the profile names `shotfleet` and `shotfleet-notary`, which never existed, and got the same "No Keychain password item found" text. **INFERENCE:** that incident was either a wrong profile name or a lock. Neither is a deletion.

### Scripts that could remove or hide it: none on this Mac

- **MEASURED.** I grepped `/Users/manu/Developer/*` (excluding vendored gems and build directories), `~/.claude/scripts`, `~/.claude/scheduled-tasks/*` (including all `keysi-*`) and `~/Library/LaunchAgents` for `notarytool store-credentials`, `delete-generic-password`, `create-keychain`, `delete-keychain`, `default-keychain`, `list-keychains -s` and `lock-keychain`. The only hits that mutate a keychain are in GitHub Actions workflows that run on GitHub-hosted runners, not on this Mac:
  - `Keysi/.github/workflows/release.yml` (`runs-on: macos-26`): temporary keychain plus `store-credentials KeysiNotary`
  - `remoti/` and `remoti-release/.github/workflows/check_and_deploy.yml` (`macos-latest`): `ci-build.keychain`

  The Keysi local scripts (`scripts/release.sh`, `ship.sh`, `cut-and-ship.sh`) only read the profile (`notarytool history`, `submit`). No `keysi-*` scheduled task calls notarytool. There is no crontab and no self-hosted Actions runner. The `subscrifi` fastlane keychain actions are vendored gem code that is never called from its Fastfile.
- **MEASURED.** The keychain search list and the default keychain are intact: user list = `login.keychain-db`, default = `login.keychain-db`.
- **INFERENCE.** Only a process holding the `com.apple.gke.notary` keychain-access-group entitlement (notarytool itself) can delete the item. A shell script would have to call `notarytool`, and none does.

## Prevention

Order by value:

1. **Keep the Mac unlocked for the length of a release.** Wrap the notarizing part of `packaging/release.sh` in `caffeinate -d -i -w $$ &` (or run the release as `caffeinate -di packaging/release.sh`). The display does not sleep, so the screen does not lock and the keybag stays unlocked. Measured lock chain: display sleep / screensaver → screen lock → keybag locked 5 min later. This does not help if the owner locks the Mac by hand (Ctrl-Cmd-Q or closing the lid). Hence item 2.
2. **Make the preflight tell a lock apart from a missing profile.** notarytool prints the same text for both cases, so `packaging/notary-check.sh` (PR #77) should print both causes and both fixes when `notarytool history` fails:
   `No usable notarytool profile "$NOTARY_PROFILE". If this Mac's screen is (or was) locked, unlock it and re-run: the item is unreadable while locked and notarytool says "not found". Only if it still fails when unlocked: xcrun notarytool store-credentials $NOTARY_PROFILE --apple-id <id> --team-id 2357A78TMR`.
   Also run the check immediately before each `notarytool submit` in `build.sh`/`pkg.sh`, not only at the start, because a release can outlive the screen lock. Unattended agents and scheduled tasks should treat this error as "Mac is locked, try again after unlock", not as "credential lost, ask the owner to recreate it".
3. **Give shotfleet its own profile, `ShotfleetNotary` (PR #77 already does this).** The owner's hypothesis that the shared profile caused the loss is not supported by the evidence above. A separate profile is still worth it for independence: Keysi can rotate or re-store `KeysiNotary` (its CI recipe does `store-credentials KeysiNotary`, today only on a GitHub runner) without breaking shotfleet, and the reverse. It should have its own app-specific password (`shotfleet-notary`, already named in `docs/owner-checklist-kvk-and-tax.md`) or its own App Store Connect team key. Files PR #77 touches: `packaging/release.sh`, `packaging/preflight.sh`, `packaging/go-live.sh`, `packaging/build.sh`, `packaging/pkg.sh`, new `packaging/notary-check.sh`, `packaging/README.md`, `LAUNCH.md`, `STATUS.md`, `DISTRIBUTION.md`, `tests/test_release_scripts.py`, and research notes. Items 1-2 add `packaging/release.sh` (caffeinate) and `packaging/notary-check.sh` (message) plus one test. Nothing in them touches a credential.
4. **Optional, for releases that must survive a locked screen: store the profile in the file-based login keychain.** Use `xcrun notarytool store-credentials ShotfleetNotary --keychain ~/Library/Keychains/login.keychain-db ...` and pass `--keychain ~/Library/Keychains/login.keychain-db` on every notarytool call. That keychain is `no-timeout` (measured), so it should stay readable while the screen is locked. **INFERENCE, not tested:** the login keychain may still lock on sleep, and storing there needs the owner, because it is a credential write. Only worth doing if items 1 and 2 are not enough.
5. **Correct Keysi `RELEASE.md` lines 140-146** (a Keysi change, not made here): the "`security find-generic-password` finds nothing, so it is gone" check is invalid, and the 2026-09-11 incident is most likely the same lock.

Not done: no keychain item was read for its secret, written or deleted. The Keysi repo was not changed, and no devices or device lock were touched.
