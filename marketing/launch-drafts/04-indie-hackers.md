# Indie Hackers

**Where:** https://www.indiehackers.com, a new post (the "Show IH" style: what you built, real numbers, one clear question). Add the product page first (https://www.indiehackers.com/products, "Add a Product") so the post can link to it; text for that is in `marketing/kit/directories.md` section 7.

## Rules to respect

- I couldn't find written posting rules for IH (not in the old research either). What the community expects, from summaries: share real numbers and what you learned, ask a real question, don't just drop a link. Help others more than you post about yourself.
- Disclose it's yours (the post is in first person, so it is).
- Don't ask for upvotes. Reply to every comment.

## Best time

A weekday morning US Eastern. Launch week starts Mon 19 Oct, so Mon 19 or Tue 20 Oct; not 13 or 14 Oct. IH posts stay visible for a day or two, so the exact hour matters less than being around to reply.

## Title

`I launched a $29 dev tool. [SALES: 0 as of 2026-10-06, re-check] sales so far, here's what I know`

If the count is still 0: `I launched a Mac tool for localized app screenshots. 0 sales so far, here's what I have`

## Post

> I'm Manu, a solo developer in the Netherlands. I have a few small apps. I built a tool for my own problem, and on 2026-10-05 I started selling it. Here's where it is, with real numbers.
>
> **The problem.** My workout app is in 18 languages. Store screenshots in 18 languages are a lot of work, so I had been cutting corners. On another app I made one English capture and only translated the captions. When I finally checked those Google Play screenshots, there were 127 problems. 103 were translated captions over an app still in English, and 15 were false alarms from a bug in my own tool, fixed in 0.1.6.
>
> **The tool.** shotfleet is a Mac command-line tool. You write one Maestro flow in English, and it runs it in every language your app has, on iOS and Android, then checks every screenshot for the wrong language, blank screens and store sizes. One run of 18 languages x 4 screens took 9 minutes on iOS and 15 on Android on my M1 Pro. It also showed me a bug: a Next button that was out of reach in four languages on small phones.
>
> **Business model.** One-time licence on Gumroad: $29 for the first 100 buyers, then $49. It covers a year of updates (a calendar year), and you can use it on up to 3 of your Macs. Free tier: check (on any screenshots, also fastlane ones) and capturing up to 2 languages. 14-day refund. No subscription, because [YOUR REASON, e.g. "you only make screenshots a few times a year, and a monthly fee for that felt wrong"].
>
> **Numbers so far.**
> - Sales: [SALES: 0 as of 2026-10-06, re-check Gumroad]
> - Releases: 0.1.0 went live on 2026-10-05; I'm on [VERSION: 0.1.6, check https://shotfleet.com/download/VERSION] now. Most of the work after launch went into making it reliable on a busy Mac (simulators that stop answering, macOS text recognition that's slow to wake up).
> - Marketing spent: $0 [CHECK: still true?]
> - Visitors: [VISITS: from site/signups.sh --visits, or leave this line out]
>
> **What I think is hard about this.**
> - The market is small: developers with apps in many languages, on a Mac, who care about screenshots.
> - Capturing screenshots is getting free (fastlane, Maestro itself, AI tools). What I think people might pay for is the check and not having to keep 18 copies of a flow. I don't know yet.
> - I'm one person, so support, tax and the product all come from the same evenings.
>
> **What I'd like to know from you.**
> - If you have an app in more than a few languages: how do you make and check the store screenshots today?
> - Would you try the free check first, or does "Mac only, needs Maestro" already lose you?
>
> https://shotfleet.com/?utm_source=indiehackers

## Before posting

- Fill every `[...]` placeholder or delete the line. Don't guess numbers.
- The 127/103/15 line needs the AnywhereRoles section live (README.md gate 1). If it isn't, say only "the captions were translated but the app under them was still in English", with no numbers.
- "On 2026-10-05 I started selling it": memory and STATUS say 0.1.0 went live 2026-10-05. Change if you count the launch date differently.
- If there's a sale by then, the title changes; keep the honesty about how small the number is.

Disclosure: first person throughout ("I built a tool... I started selling it").
