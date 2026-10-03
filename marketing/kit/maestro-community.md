# Maestro community kit (Slack, awesome-maestro, docs)

Owner: Manu posts. Nothing here has been posted. Written 2026-10-02.
Where: Maestro Slack, channel `#maestro-questions` (join at https://slack.maestro.dev/; the docs community page names the channel); PRs to https://github.com/ludovicobesana/awesome-maestro and https://github.com/mobile-dev-inc/maestro-docs.
Ready when: you are a member and have read the workspace and channel rules (not found by research; read them first). For the answers: a real question has been asked. For PRs: article 2 is live on the domain and its TO VERIFY list is ticked; the Maestro team has answered the paid-tools question below.

## Rules for yourself

1. Weeks 1 and 2: answers only, no link, no product name. Answer a question only if you can run the steps yourself first.
2. Mention shotfleet only if someone asks "is there a tool for this?", and say in the same sentence that you built it and that it is paid after 2 languages.
3. Never post the same text in two channels. Never DM anyone who did not write to you first.
4. Do not say Maestro "recommends one flow per locale". The current docs recommend tags plus `--device-locale`. Do not say or imply Maestro endorses shotfleet or that you are a partner.
5. Every answer below states what it was written against; before posting, run the commands on the Maestro version you name in the answer (the version installed on the dev Mac is 2.0.10; current upstream is 2.11.0, per research/limits-text.md).

Docs read on 2026-10-02: https://docs.maestro.dev/maestro-flows/flow-control-and-logic/test-in-different-locales (locale only via `--device-locale` on `maestro start-device` and `maestro cloud`, not `maestro test`; no place in a flow), launchApp (`arguments` map, `permissions`, `clearState`), parameters-and-constants (three variable sources, subflow constants override parent parameters), runFlow (`when: platform:`).

---

## Answer 1: "How do I run my flow in another language?"

> Two documented routes and one per-app route, depending on what you need.
>
> 1. Device locale: `maestro start-device --platform android --device-locale fr_FR` (language_COUNTRY, with an underscore), then `maestro test --include-tags french .maestro/`. The docs say `--device-locale` is accepted by `start-device` and `cloud`, not by `maestro test`, and that a flow itself has no place to set the locale. So you start or restart a device per language.
> 2. iOS, per app: pass the language as launch arguments in the flow:
>    ```yaml
>    - launchApp:
>        clearState: true
>        arguments:
>          AppleLanguages: "(de)"
>          AppleLocale: "de_DE"
>    ```
>    iOS reads those two keys at launch, so only your app changes language, not the simulator.
> 3. Android 13+ (API 33), per app: `adb shell cmd locale set-app-locales <package> --locales de` before the flow starts.
>
> Whichever you pick, open the first screenshot of each language. A run that is in the wrong language still passes.

Verify before posting: route 2 and 3 on the Maestro version you state (see article 2 TO VERIFY items 1, 3, 4). Do not post route 3 if `cmd locale set-app-locales` does not work on your emulator.

## Answer 2: "I pass -e LOCALE=de but my screenshots are in English"

> Two things to check. First, a default in the flow header can win over the command line. Someone documented this on Maestro 2.10: the flow had `env: { LOCALE: en }`, and every run came out in English whatever `-e` said (https://github.com/RogerioDoCarmo/morse_app/pull/216). Remove the default and take the value only from `-e`. Maestro's parameters page says constants defined in a subflow override same-name parameters from the parent, which points the same way.
> Second, the order: `maestro --device <id> test -e KEY=VALUE flow.yaml`. In that PR the `-e` before `test` failed silently.
> And look at the images, not the file count; that is how it was found.

Verify before posting: reproduce on your version. If you cannot, change "wins over" to "someone reported it wins over" (already hedged) and say you could not reproduce it.

## Answer 3: "tapOn: 'Next' fails when the app is in another language"

> Text selectors match what is on screen, so a translated label is a different string. Three options, easiest first:
> 1. Tap by `id:` (accessibility identifier on iOS, resource id on Android). It does not change with the language.
> 2. Put the label in a variable and pass it per language: `tapOn: ${NEXT_LABEL}` with `-e NEXT_LABEL=Weiter`.
> 3. Text selectors are regular expressions, so you can match several languages at once: `tapOn: "(Next|Weiter|次へ)"`.
> If the failure is a button that exists but cannot be tapped in one language, check that the page can scroll: `scrollUntilVisible` does nothing on a page with no scroll container. I hit exactly that once on a small phone in Japanese, Korean, Chinese and Arabic.

Verify before posting: option 3 on your Maestro version (regex matching of `text`); the last sentence is the true story from article 3 (commit 687ffccd), so keep it first person and short.

## Answer 4: "The permission dialog is not dismissed when the device is not in English"

> System permission alerts are drawn by the OS in the device language, not your app's. If you only changed the app's language, the alert stays in the device's language (English, in my case on iOS; I measured it with Maps). So a tap on a translated label will not find it.
> Simplest fix is to not show it: start the flow with
> ```yaml
> - launchApp:
>     permissions:
>       all: allow
> ```
> If you do need the real alert, write that one tap in the device language. There is an open Maestro issue about English-only permission dismissal (#2654 when I last looked; check its status).

Verify before posting: the `permissions: all: allow` block on the platform you answer for; re-check issue #2654 is still open. Do not claim you tested Android alerts.

## Answer 5: "On Android the app language resets or is not applied"

> Per-app languages exist from Android 13 (API 33); on older emulator images there is nothing to set. If it worked and then reset: `clearState` wipes the app's data and the per-app language with it. Run `adb shell pm clear <package>` first, set the language, then launch without `clearState`. The language list is also limited to what the app ships (its `values-xx` folders or `locale_config.xml`), so a language that is not in the APK will quietly fall back.

Verify before posting: the `pm clear` then `set-app-locales` order on an API 33+ emulator (article 2 item 5). The "limited to what the app ships" sentence comes from a community write-up, not Android's page; reproduce or remove it.

## Answer 6: "Running one flow on several devices at the same time"

> On Maestro 2.0.10 I saw two things. Two separate `maestro test` processes, one per device, shared a host port (7001) and could drive each other's device. One run with `--device a,b test dir --shard-split 2` avoids that, but then you do not control which flow lands on which device and a flow cannot read its shard index; I mapped flows to devices from the debug log afterwards. Newer versions are said to pick a port per shard, so retest on yours before you rely on any of this.

Verify before posting: both observations on the version you name (research/limits-text.md records the 2.0.10 port range and the random port in 2.11). If you cannot run it now, do not post it.

If someone then asks "is there a tool for this?": use the disclosure line below, once.

> I built one, shotfleet, so take it with that in mind. It rewrites the text selectors of an English flow per language and runs the languages in parallel on simulators and emulators. It is Mac-only (Apple silicon), free for 2 languages and paid after that. Happy to share the config if useful, no pressure.

(No link in the first reply. Give the URL only if they ask where to find it.)

---

## The question to ask the Maestro team (once, in `#maestro-questions` or as a GitHub issue on maestro-docs)

> Hi, a small question about the community projects page. It lists free and open-source projects. I have a Mac command line tool built around Maestro that is closed source, free for a small tier and paid beyond that (it runs one flow in many languages). Would a project like that be welcome on the community projects page or in the awesome list, or are those for free and open projects only? If not, a link to a how-to article on the community articles page would be enough for me. I do not want to open a PR that is out of scope.

Why: the page lists only free and open projects and states no submission route (research/marketing-research.md 1.9). Past PRs took about five weeks to merge. Do not open a PR for the projects page until they answer.

## awesome-maestro PR text

Repo: https://github.com/ludovicobesana/awesome-maestro (CC0; sections: Articles, Tools and Integrations, Showcases, Talks, Guides, Example Projects, Community Contributions, Official Resources). Entry format in the file: `- [Name](url) - One sentence.` CONTRIBUTING.md has no mandatory entry template (read 2026-10-02): keep the PR to one line and one purpose. The list already contains a paid cloud (BrowserStack), so a paid tool is plausible.

First PR (article, safer): add under `## Articles`:

```
- [Run one Maestro flow in every language](https://shotfleet.com/maestro-one-flow-every-language?utm_source=awesomemaestro) - Setting the locale per run on iOS and Android, and four traps that produce English screenshots by mistake.
```

PR title: `Add article: run one Maestro flow in every language`

PR body:

> Adds one article to Articles. It covers `--device-locale`, per-app locales on iOS and Android, and what to check when runs come out in the wrong language. Disclosure: I wrote it and I also make a paid tool in this area, which the article mentions once near the end. The article is useful without it. Happy to move or reword the entry.

Second PR (tool, only if the Maestro team or the list owner says paid tools are fine), under `## Tools and Integrations`:

```
- [shotfleet](https://shotfleet.com/?utm_source=awesomemaestro) - Mac command line tool that runs one English Maestro flow in every language an app ships, on iOS simulators and Android emulators, and checks the screenshots. Free for 2 languages, paid licence for all.
```

PR body: same disclosure, plus "closed source, Apple silicon Mac only, requires Maestro 2.x and Java 17+."

## Docs community article pitch (maestro-docs)

Target: `resources/community/articles.md` in https://github.com/mobile-dev-inc/maestro-docs (page: https://docs.maestro.dev/extra-materials/community/articles). It is a set of card tables per section (Getting Started, Best Practices, React Native, ...), each row a title, a cover image and a link. Precedent: a PR that linked a community article was merged after about five weeks (PR #149).

Open the PR (or an issue first, to ask which section) with:

> Title: Add community article: run one Maestro flow in every language
>
> This adds one card linking a community article on running a flow in several languages on iOS and Android: `--device-locale`, per-app locales, and traps such as header `env` defaults hiding `-e` values. Section: I suggest "Best Practices", or a new "Localization" heading if you prefer. Disclosure: I wrote it, and I make a paid third-party tool in this area; the article mentions it once at the end and everything before that is plain Maestro and adb. If a card needs a cover image I will supply one at the size you prefer. Happy to change anything.

Add one row copied from an existing card in the same table, with the article title, a cover image URL (create one on the domain, for example the review grid) and the article URL. Check the column order in that table's header before pasting.

Do not claim the article is approved or listed anywhere until the PR is merged.
