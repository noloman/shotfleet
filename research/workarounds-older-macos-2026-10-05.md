# Getting real evidence on older macOS and a clean Mac without owning one (2026-10-05)

Question: shotfleet 0.1.1 is built for macOS 13 or later (Mach-O minimum 11.0 and 13.0), and has run on macOS 27.0 (this Mac) and on GitHub-hosted macOS 14.8.9 and 15.7.9 (`research/limits-platform-reach-2026-10-05.md`, hosted-runner section). Unproven: macOS 13, macOS 26.0 to 26.2, a clean Mac (no Homebrew, Java, Maestro, Xcode), Gatekeeper on a browser download, the licence call from the packaged program elsewhere, other Xcode versions. What is the cheapest and safest way to get evidence?

Nothing here was downloaded beyond small metadata (Apple's IPSW list, GitHub's registry manifests, web pages), no VM or tool was installed, no VM was run, no build, no CI, no money. Tags: **[M]** measured today; **[S]** read on a web page (URL, 2026-10-05); **[I]** my inference, a hypothesis.

## Recommendation (first)

1. **Run two or three free macOS VMs with Tart on a quiet Mac: macOS 13.6, 26.0 and 26.2 "vanilla" images (no Homebrew, no Java, no Xcode).** Cost: $0 in money; about 65 GB of download (18.0 + 24.0 + 23.3 GB compressed, [M] from the registry manifests), 6 GB RAM and about 60 GB of free disk at a time (one VM at a time, delete after use), roughly 2 to 3 hours of elapsed time, mostly the download (my estimate [I], depends on the line). Hands-on time about 30 minutes. It proves, per guest: `install.sh` works, `--version` starts (dyld, Swift runtime, expat), `doctor` runs to the end on a Mac with nothing installed, the bundled `ocr` reads text, `check` runs, the licence call reaches Gumroad, and (with one Safari download and one `spctl --global-enable`) what Gatekeeper does with a browser download. All of it is scripted by `research/proposed-selftest/selftest.sh`.
2. **Do it after the release gate, not now.** Measured at 15:3x today: 36 GB free disk (not 85), swap 6.3 of 7.2 GB used, load average 799. A VM would thrash the gate and not fit. The coordinator's approval is needed for the downloads and the Homebrew install of Tart (see "What needs approval").
3. **Ask a person with an older Mac to run the same script** (`sh selftest.sh --download`, 1 minute, one result block to paste back): free, and it is the only path to a real machine without paying. See section (c).
4. **Paid fallback, only if a VM result is ambiguous: Scaleway Mac mini M1, about EUR 2.64 for the 24-hour minimum [S, I]** (real hardware, macOS 13 offered). AWS EC2 Mac costs $15.60 minimum for the same. **Neither cloud offers 26.0 to 26.2** (AWS keeps the latest 26.x AMI only [S]); only a VM or a person's Mac can.
5. **Already done today, free: the clean-environment run on this Mac** (section d): `selftest.sh --hide-tools` passed (install, `--version`, `doctor`, `check`) with an empty environment, Homebrew, Java, Maestro and Android hidden. It proves less than a VM (same OS, 27.0), see the table.

## Comparison

| Option | macOS 13 | macOS 26.0-26.2 | Clean machine | Gatekeeper on a browser download | Cost of one 2-hour test | Main risk |
|---|---|---|---|---|---|---|
| **A. Tart VM** (Cirrus Labs, Virtualization.framework) | yes, 13.6 [S] | yes, tags 26.0, 26.1, 26.2 [M] | yes (vanilla) | yes, but Tahoe/Sequoia vanilla templates disable it: re-enable first [M] | $0; 18 to 24 GB download each | disk and RAM on this Mac; the image is not a real buyer's Mac |
| B. UTM or VirtualBuddy (GUI, same framework) | yes, IPSW 13.6 12.9 GB [M] | yes, IPSW 26.0 18.3 GB, 26.1 18.7 GB, 26.2 18.7 GB [M] | yes, after Setup Assistant by hand | yes | $0; smaller download, 30 to 40 min of clicking per guest | manual setup, no scripting |
| C. Apple's sample code | same as B | same | same | same | $0, but needs an Xcode build [I] | not worth it: B does the same without a build |
| D. AWS EC2 Mac (`mac2.metal`, M1) | yes, Ventura AMI (13.2 or later on M2) [S] | **no**, latest 26.x only [S] | **no**: AMI ships Homebrew, Command Line Tools, AWS CLI [S] | yes (real Mac, no VM) | **$15.60** (0.65/h, 24 h minimum) + EBS [S] | account quota for Mac hosts may be 0 for new accounts [I]; 6 to 20 min boot [S] |
| E. Scaleway Mac mini M1 | yes (Ventura, Sonoma, Sequoia offered) [S, search result] | **no** (Tahoe not listed) [S] | partly (fresh macOS, admin) [I] | yes | **about EUR 2.64** (0.11/h, 24 h minimum, 8 GB RAM) [S, I] | pricing page is JavaScript; OS list and minimum from a search summary |
| F. MacStadium | Ventura "on request" [S] | no | yes | yes | **$109** (monthly billing only) [S] | no hourly option |
| G. MacinCloud pay-as-you-go | Ventura [S] | no | no: shared managed account, no admin [S] | partly | $25 minimum prepay (25 h at $1) [S] | not a clean account |
| H. GitHub hosted runner (manual) | **no** (oldest is macos-14) [S] | **no** (`macos-26` is the newest 26.x) [S, I] | no (Homebrew, Java on the image) | no (curl sets no quarantine) | $0.062 per minute, about $0.3 to 0.5 per OS [S] | cannot reach the two unproven versions |
| I. Someone's older Mac + `selftest.sh` | whatever they have | whatever they have | possible | yes (they download in Safari) | $0 | needs a willing person |
| J. Clean HOME + `sandbox-exec` on this Mac | no (27.0) | no | partly (no Homebrew etc., but Xcode, Gatekeeper state and OS libraries are this Mac's) | no | $0, 1 minute | proves less (section d) |

Orka (MacStadium's Kubernetes layer) is an enterprise product and its free "Orka Desktop" is another front end to the same Apple framework [S: devopsdigest, 2026]; not evaluated further.

## (a) Local VMs on Apple silicon: the facts

- **Host and guest versions.** Virtualization.framework runs guests no newer than the host. M1, M2 and M3 hosts can virtualize macOS 12.0.1 and later; M4 hosts only 13.4 and later; macOS 11 cannot be virtualized at all ([eclecticlight.co, 2024-11-14](https://eclecticlight.co/2024/11/14/m4-macs-cant-virtualise-older-macos/) and [9to5mac, 2024-11-18](https://9to5mac.com/2024/11/18/m4-macs-virtual-machines-macos/)). This Mac is an **M1 Pro (MacBookPro18,3), macOS 27.0** [M], so 13.6, 26.0, 26.1 and 26.2 guests are in range. That a macOS 27 host boots a 26.0 or 13.6 guest is [I]: Cirrus builds its images on current hosts and this is the normal direction.
- **Restore images from Apple's catalog [M]** (ipsw.me's list for VirtualMac2,1, fetched 2026-10-05; HEAD requests to Apple's CDN answered 200 with these sizes today, nothing downloaded). ipsw.me marks every row "unsigned", which matters for real devices, not for VMs [I: Tart's own Ventura image was built from 13.6, so old IPSWs still install].

  | macOS | Build | Released | Size | URL |
  |---|---|---|---|---|
  | 13.6 (newest 13 IPSW) | 22G120 | 2023-09-21 | 12.9 GB | https://updates.cdn-apple.com/2023FallFCS/fullrestores/042-55833/C0830847-A2F8-458F-B680-967991820931/UniversalMac_13.6_22G120_Restore.ipsw |
  | 26.0 | 25A354 | 2025-09-15 | 18.3 GB | https://updates.cdn-apple.com/2025FallFCS/fullrestores/093-37622/CE01FAB2-7F26-48EE-AEE4-5E57A7F6D8BB/UniversalMac_26.0_25A354_Restore.ipsw |
  | 26.1 | 25B78 | 2025-11-03 | 18.7 GB | https://updates.cdn-apple.com/2025FallFCS/fullrestores/089-04148/791B6F00-A30B-4EB0-B2E3-257167F7715B/UniversalMac_26.1_25B78_Restore.ipsw |
  | 26.2 | 25C56 | 2025-12-12 | 18.7 GB | https://updates.cdn-apple.com/2025FallFCS/fullrestores/093-37399/E144C918-CF99-4BBC-B1D0-3E739B9A3F2D/UniversalMac_26.2_25C56_Restore.ipsw |

  The IPSW list has no 13.7.x (those were never offered as IPSW for VMs): 13.6 is the newest macOS 13 guest. A real macOS 13 buyer is probably on 13.7.8 [I]; 13.6 still tests the dyld, Swift runtime and Vision questions.
- **Tart** ([tart.run](https://tart.run/quick-start/)): free for personal workstations, a paid licence only above 100 CPU cores in server use ([licensing](https://tart.run/licensing/), 2026-10-05). Prebuilt images at `ghcr.io/cirruslabs/`: `macos-ventura-vanilla` (tag 13.6 = latest, 18.0 GB compressed, uploaded 2025-02-15), `macos-tahoe-vanilla` with tags **26.0** (24.0 GB, 2025-09-25), **26.1** (23.1 GB, 2025-12-05), **26.2** (23.3 GB, 2025-12-16) [M, registry manifests]; Sonoma 14 and Sequoia 15 exist too. Uncompressed disk is 50 GB each, sparse [M, manifest annotation]. Login `admin`/`admin`, SSH enabled, passwordless sudo, auto-login, default 2 CPUs and 4 GB RAM [S, quick-start]. "Vanilla" has no Homebrew and no other software [S, search result]; "base" adds Homebrew (not clean).
- **Gatekeeper caveat [M]:** the Cirrus template for Tahoe and Sequoia vanilla runs `sudo spctl --global-disable` and checks `assessments disabled` (raw template files `vanilla-tahoe.pkr.hcl`, `vanilla-sequoia.pkr.hcl` in `cirruslabs/macos-image-templates`); Ventura, Sonoma and Monterey templates do not. Whether the older Tahoe tags (26.0 to 26.2) were built from a template with that line is unknown [I]: run `spctl --status` in the guest and `sudo spctl --global-enable` before the Gatekeeper test. `selftest.sh` prints the status.
- **UTM** ([docs](https://docs.getutm.app/guest-support/macos/)): macOS 12+ guests through Virtualization.framework, IPSW chosen or fetched automatically; no save states before macOS 14, no clipboard sharing before 15. **VirtualBuddy** ([repo](https://github.com/insidegui/VirtualBuddy)): BSD-2, macOS 13+ host, macOS 12+ guests, picks IPSWs from Apple's servers or a URL, `brew install --cask virtualbuddy`. Both are GUI: you click through Setup Assistant yourself. Tart's images skip that.
- **Licence:** Apple's macOS licence allows up to 2 additional macOS copies in VMs for development, testing and personal use, and the kernel allows 2 running macOS VMs ([khronokernel, 2023-08](https://khronokernel.com/macos/2023/08/08/AS-VM.html), quoting the Ventura SLA; I did not re-read the macOS 27 licence [I]). Fine for one guest at a time.
- **Cost on this Mac:** the VM is a file of up to 50 GB (actual use maybe 25 to 30 GB after the pull [I], measure with `du -sh ~/.tart/vms/<name>`), 4 to 6 GB RAM, 3 to 4 cores. Today: 36 GB free, swap nearly full [M]. So: one VM at a time, delete each, and wait for the gate. If free disk stays under 60 GB, put Tart's folder on an external SSD (`TART_HOME`, from memory of Tart's docs [I]).
- **Xcode, simulators, Maestro in a guest.** Xcode and the iOS Simulator run inside macOS VMs on Apple silicon (secondary sources, and GitHub's own macOS runners are such VMs and ran `simctl` in the 2026-10-05 run) [S, I]. The Android emulator does not: nested virtualization is supported only on M3 or M4 hosts with macOS 15 or later and only for Linux guests ([Tart FAQ](https://tart.run/faq/)), and this host is an M1 Pro. So a VM can give start, `doctor`, `check`, Gatekeeper and a clean user; it cannot give an Android run, and an iOS run needs an Xcode inside the guest (Cirrus has `xcode` image variants, large, not evaluated) and the real fixture build: not part of the cheap test.
- **What a VM cannot show:** real hardware (Neural Engine, GPU, power), a real buyer's configuration (FileVault, MDM, antivirus, a localised system), timing, Apple's Gatekeeper reputation for a fresh download on a physical Mac (the VM does ask Apple's servers, so it is a good proxy, but it is not the same Mac) [I]. And what `doctor` does on a Mac with **no Command Line Tools**: `swiftc` and `xcrun` are stubs there that may open a GUI install prompt [I]; the vanilla guest is the only place in this plan that shows it, and `selftest.sh` marks a hang as FAIL (150 s limit).

## (b) Cloud Macs: real prices

| Provider | Offer | Price | Minimum | macOS | Sources |
|---|---|---|---|---|---|
| AWS EC2 Mac | `mac2.metal` M1, 8 cores, 16 GB; `mac2-m2` 24 GB; `mac2-m2pro` 32 GB; `mac-m4` 24 GB, `mac-m4pro` 48 GB | `mac2.metal` $0.65/h, `mac2-m2.metal` $0.878/h (us-east-1, on-demand, per Dedicated Host) | **24 h per host**, billed per second after; one instance per host | AWS AMIs: 13 (all types; M2 needs 13.2+), 14, 15, 26; `get-parameter` gives only the latest image per major version | [EC2 Mac](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-mac-instances.html), [AMI notes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/macos-ami-overview.html), [SSM](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/macos-ami-ids-parameter-store.html), [Vantage](https://instances.vantage.sh/aws/ec2/mac2.metal) |
| Scaleway | Mac mini M1 8 GB 256 GB, M2 16 GB, M2 Pro, M4, M4 Pro; Paris only | M1 EUR 75/month or EUR 0.11/h; M2 EUR 0.17/h | 24 h (Apple licence) [search summary] | Ventura, Sonoma, Sequoia (search summary, not the pricing page) | [pricing](https://www.scaleway.com/en/pricing/apple-silicon/), [search](https://www.scaleway.com/en/docs/apple-silicon/quickstart/) |
| MacStadium | Mac mini M2.S $109 to M4.L $349 per month | monthly or annual only | 1 month | latest; Sonoma or Ventura on request | [pricing](https://www.macstadium.com/pricing) |
| MacinCloud | Pay-as-you-go managed Mac mini M1/M2/M4 | $1/h with 25 h prepaid, or $4/day with 7 days | 25 h or 7 days, non-refundable | Sequoia, Sonoma, Ventura; no SIP or admin | [PAYG](https://www.macincloud.com/pages/payg.html) |
| GitHub hosted | `macos-14`, `macos-15`, `macos-26` arm64 3 vCPU 7 GB; `macos-15-intel`, `macos-26-intel`; larger 12-core Intel $0.077/min, M2 Pro $0.102/min | **$0.062/min**, rounded up per job; not free for public repos | none | **no macOS 13 or older listed**; `xcode-27` label in preview | [runners](https://docs.github.com/en/actions/reference/runners/github-hosted-runners), [prices](https://docs.github.com/en/billing/reference/actions-runner-pricing) |

Notes. (1) AWS's AMIs include Homebrew, Command Line Tools and AWS CLI by default [S], so an EC2 Mac is not a clean machine unless the script hides them (`--hide-tools`). (2) AWS release notes list Ventura 13.7.8 as the last macOS 13 update (2025.09.04) and the 2026.09 notes no longer list it [S]; whether the Ventura AMI is still launchable is [I], check before paying. (3) New AWS accounts often have a quota of 0 for Mac Dedicated Hosts and need a request [I, from memory]. (4) Cost of ONE 2-hour test: AWS $15.60 (+ about $0.3 EBS), Scaleway about EUR 2.64, GitHub about $0.5 per OS (and it cannot reach 13 or 26.0-26.2), MacStadium $109, MacinCloud $25, VM $0. (5) Prices are from search summaries or pages fetched today; I did not log in anywhere or create an account.

## (c) A person with an older Mac: the one-command self-test

`research/proposed-selftest/selftest.sh` (proposed, not in `tools/`). Send it as a file; the person runs one line in Terminal:

```
sh selftest.sh --download
```

(or `sh selftest.sh --tarball shotfleet-macos-arm64.tar.gz` for a file they already have, which downloads nothing). It prints the macOS version, build and architecture; makes a throwaway HOME under `/tmp`; installs the release there as `install.sh` does (checksum checked, no link on the PATH, nothing outside the folder); runs `--version`, `doctor` (never `--fix`, 150 s limit) and `check` on two screenshots it draws itself (so the person needs no files); prints one block between `===== shotfleet selftest: PASS|FAIL =====` and `===== end =====`; deletes the folder. `doctor` makes the one version-check request to shotfleet.com that it always makes. Options: `--quarantine` (mark the program as browser-downloaded), `--licence-probe` (one made-up key to Gumroad's verify endpoint, off by default), `--hide-tools`, `--keep`. For the Gatekeeper question the person downloads `https://shotfleet.com/download/shotfleet-macos-arm64.tar.gz` in Safari, double-clicks it, then runs `sh selftest.sh --folder ~/Downloads/shotfleet`: `ditto` keeps the quarantine flag [M] and the block says `quarantine flag on the program: yes`. Message to send, in two lines: "Could you run this on your Mac? Open Terminal, `cd` to where you saved the file, run `sh selftest.sh --download`, and paste the block between the ===== lines. It installs into a temporary folder and deletes it; it changes nothing else."

Tested here [M]: `sh -n` clean; one real run on this Mac (macOS 27.0, M1 Pro) from the 0.1.1 tarball in `/Users/manu/Developer/shotfleet-rc-build/0.1.1/`, in a throwaway HOME with `--hide-tools`: PASS (`shotfleet 0.1.1`, `doctor` exit 2 with Maestro, Java and Android reported missing, "text recognition ready in 1 s", iOS runtime 27.0 found; `check` on the 2 drawn 1290x2796 screenshots: 0 problems, exit 0), 44 s; a second run with `--quarantine`: PASS; no argument or a wrong option exits 2 with a message. `--download` and `--licence-probe` were not run (no network use beyond `doctor`'s own request). The temporary folders were removed (checked).

## (d) Clean account on THIS Mac, without sudo

How it was done on 2026-10-03 (`STATUS.md` row D1): a throwaway `HOME`, `SHOTFLEET_HOME` and `ANDROID_HOME`, and a `sandbox-exec` profile that hid this Mac's Java, SDK and Homebrew tools, because `ANDROID_HOME` alone does not hide them (`find_sdk` and `find_java` also look in absolute Homebrew paths). The profile itself was not saved; `selftest.sh --hide-tools` rebuilds one: `(allow default)` plus `(deny file-read* file-write* ...)` for `/opt/homebrew`, `/usr/local`, `/Library/Java` and the Android, Maestro, shotfleet, sdkman and Gradle folders of the real home, and runs the program with `env -i` and `PATH=/usr/bin:/bin:/usr/sbin:/sbin`. Measured: it worked (doctor reported Maestro, Java, adb, emulator and the rest MISSING although this Mac has them).

| | Clean HOME + sandbox here | A real clean Mac or a vanilla VM |
|---|---|---|
| Install from the tarball, `--version`, `doctor` end to end, `check`, Vision/ocr | proves it on macOS 27.0 | proves it on that OS |
| No Homebrew, Java, Maestro, Android tools | proves (hidden, `env -i`) | proves (absent) |
| Older macOS libraries (dyld, Swift runtime, expat, Vision languages) | **no**: this Mac's | yes |
| No Xcode, no Command Line Tools (stub prompt, `xcrun` behaviour) | **no**: Xcode is here (doctor found simctl and the iOS 27.0 runtime) | yes, vanilla guest only |
| Gatekeeper, quarantine on a browser download | no (can only set the flag by hand: `--quarantine`) | yes |
| A second macOS user (own keychain, own `~/Library`) | no (`sysadminctl -addUser` needs sudo, so not done) | yes |
| Writes outside the throwaway home | none seen; real `~/.shotfleet` untouched | n/a |

So (d) is a cheap regression screen, worth running before every release (one minute), not a substitute for A or I.

## Runbook for the recommendation (Tart, after the gate; every step below needs the coordinator's yes first)

Preconditions (read, do not skip): the release gate is finished and no other device job holds `/tmp/shotfleet-devices.lock`; `df -h /` shows 60 GB or more free (or `TART_HOME` points at an external disk); `uptime` load under 20 and swap mostly free. Per `feedback_verify_ownership_before_kill_or_delete.md`: the VMs and `~/.tart` are created by this work, and only those names are ever deleted. Give every step a time limit; a VM run is not a device job but it still must not starve other work.

```
# 0. tool (about 20 MB; approval needed)
brew install cirruslabs/cli/tart
export TART_HOME="$HOME/.tart"           # or /Volumes/<external>/tart
df -h "$TART_HOME" | tail -1             # need >= 60 GB free

# 1. macOS 13.6, vanilla (18.0 GB compressed, 50 GB disk, sparse)
tart clone ghcr.io/cirruslabs/macos-ventura-vanilla:13.6 sf-ventura
du -sh "$TART_HOME/vms/sf-ventura"       # record the real size
tart set sf-ventura --cpu 4 --memory 6144
tart run sf-ventura &                    # window needed for the Safari step; --no-graphics for ssh only
sleep 60; tart ip sf-ventura             # wait for an address
```
Copy the script and the tarball in (no browser, no quarantine flag):
```
IP=$(tart ip sf-ventura)
scp research/proposed-selftest/selftest.sh admin@$IP:~/        # password: admin
ssh admin@$IP 'sw_vers; spctl --status; uname -m; ls /usr/bin/swiftc /Library/Developer/CommandLineTools 2>&1 | head -3'
ssh admin@$IP 'sh selftest.sh --download --licence-probe' | tee research/selftest-result-ventura-13.6.txt
```
The Gatekeeper step (in the VM window; two minutes):
```
ssh admin@$IP 'spctl --status'           # if "assessments disabled": sudo spctl --global-enable, then check again
# in the VM: Safari -> https://shotfleet.com/download/shotfleet-macos-arm64.tar.gz -> double-click it in Downloads
ssh admin@$IP 'xattr -p com.apple.quarantine ~/Downloads/shotfleet/shotfleet'   # must print a value
ssh admin@$IP 'sh selftest.sh --folder ~/Downloads/shotfleet'
# also by hand in the VM Terminal: ~/Downloads/shotfleet/shotfleet --version  (note any Gatekeeper dialog: that is the buyer's first run)
```
The user-facing install path, once (this is what the site tells buyers to do; it puts a link in `~/.local/bin`):
```
ssh admin@$IP 'curl -fsSL https://shotfleet.com/install.sh | sh; ~/.local/bin/shotfleet --version; ~/.local/bin/shotfleet doctor' | tee research/selftest-install-ventura-13.6.txt
```
Then stop and delete, and repeat for Tahoe with the other tags (one VM at a time):
```
tart stop sf-ventura; tart delete sf-ventura
tart clone ghcr.io/cirruslabs/macos-tahoe-vanilla:26.0 sf-tahoe-260     # 24.0 GB; same steps; then delete
tart clone ghcr.io/cirruslabs/macos-tahoe-vanilla:26.2 sf-tahoe-262     # 23.3 GB; 26.1 (23.1 GB) only if 26.0 and 26.2 differ
```
Pass criteria per guest: the block says PASS; `--version` is `shotfleet 0.1.1` (or the current release); `doctor` exit 0 to 2 and no dyld, "Library not loaded" or "Symbol not found"; "text recognition ready"; `check` exit 0 or 1 with a report; licence probe `ok`; the Safari-downloaded program starts with quarantine flag `yes`; and the sw_vers lines are pasted into the evidence note. Expected and NOT a failure: `doctor` exit 2 (nothing installed), Vision unable to read some languages on older macOS (macOS 14 could not read Catalan on 2026-10-05).

Expected time: Ventura pull 18 GB (about 25 min at 100 Mbit/s, 5 min at 500 Mbit/s [I]), boot and copy 5 min, run 5 min, Gatekeeper 5 min. Tahoe: 24 GB each, same. Total elapsed 1.5 to 3 hours, hands-on about 30 minutes. Disk: peak one VM (about 30 GB, see `du`) plus Tart's cache.

Risks and fixes. (1) The pull is interrupted: rerun `tart clone`, it resumes layers [I]. (2) `tart ip` empty: wait or use the VM window. (3) Vision text recognition slower in a VM: GitHub's runner VMs read text in 1 s [M], so expected fine. (4) Tahoe vanilla Gatekeeper disabled: see above. (5) macOS 26 guests ask for "Local Network" or other prompts on first launch [I]: answer in the window. (6) The VM competes with another session: abort with `tart stop`. (7) A guest older than the host fails to boot: fall back to B (UTM or VirtualBuddy with the IPSW above) or to section (c). (8) Never type an Apple ID or any real credential into a guest; the vanilla images need none.

## What remains unproven after this plan

- A real (non-VM) Mac older than 27: only section (c) or a paid cloud Mac (D or E) gives it; macOS 26.0 to 26.2 on real hardware is reachable only through a person.
- macOS 13.7.x specifically (the IPSW is 13.6), macOS 12 and older (0.1.1 does not claim them).
- Simulators on other Xcode versions, iOS 26.x runtimes on older macOS, any Android emulator run: need a Mac with the Xcode, not covered by the cheap test.
- A refunded key on the real Gumroad API; the licence probe only shows that a made-up key is refused.
- Rosetta, an Intel Mac, MDM or antivirus environments, FileVault.
- Whether Homebrew-less `doctor --fix` (downloads Maestro, Java, Google's tools, 350 MB) works from a clean guest: it is a large download and `selftest.sh` deliberately never runs it; one manual `doctor --fix --yes` in a vanilla guest would settle it.

## Sources (fetched 2026-10-05)

[tart.run/quick-start](https://tart.run/quick-start/), [tart.run/faq](https://tart.run/faq/), [tart.run/licensing](https://tart.run/licensing/); Cirrus templates `cirruslabs/macos-image-templates` (`templates/vanilla-*.pkr.hcl`, raw files, read by script); `ghcr.io` registry manifests for `cirruslabs/macos-*-vanilla` (size and tags; token-less public read); [ipsw.me API](https://api.ipsw.me/v4/device/VirtualMac2,1?type=ipsw) and HEAD requests to `updates.cdn-apple.com`; [UTM macOS guests](https://docs.getutm.app/guest-support/macos/); [VirtualBuddy](https://github.com/insidegui/VirtualBuddy); [eclecticlight](https://eclecticlight.co/2024/11/14/m4-macs-cant-virtualise-older-macos/); [khronokernel](https://khronokernel.com/macos/2023/08/08/AS-VM.html); AWS, Scaleway, MacStadium, MacinCloud and GitHub pages as linked above; local measurements by `df`, `sysctl`, `uptime`, `selftest.sh`.
