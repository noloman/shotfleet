# Store listing locale codes (fetched 2026-10-01)

## 1. App Store (fastlane deliver)

Source of truth for `deliver` folder names: `FastlaneCore::Languages::ALL_LANGUAGES`
(`Deliver::Languages::ALL_LANGUAGES` aliases it; `Deliver::Loader::LanguageFolder` matches folder
names case-insensitively against it, plus special dirs `appleTV`, `iMessage`, `default`).

- File: https://github.com/fastlane/fastlane/blob/master/fastlane_core/lib/fastlane_core/languages.rb
  (raw: https://raw.githubusercontent.com/fastlane/fastlane/master/fastlane_core/lib/fastlane_core/languages.rb)
- Looked at: master @ `fb7e738d0e8dc20fde488287f593dc40657163db` (2026-09-30); latest release 2.240.1 (2026-09-15).
- File last changed 2026-05-06 by "[deliver] Add support for 11 new App Store Connect locales (#29959)".
  Whether 2.240.1 contains #29959 was not verified (commit is before the release date, so very likely yes; check the tag).
- Loader: https://github.com/fastlane/fastlane/blob/master/deliver/lib/deliver/loader.rb

Exact source line:

```ruby
ALL_LANGUAGES = %w[ar-SA bn-BD ca cs da de-DE el en-AU en-CA en-GB en-US es-ES es-MX fi fr-CA fr-FR gu-IN he hi hr hu id it ja kn-IN ko ml-IN mr-IN ms nl-NL no or-IN pa-IN pl pt-BR pt-PT ro ru sk sl-SI sv ta-IN te-IN th tr uk ur-PK vi zh-Hans zh-Hant]
```

(50 codes, matching the 50 languages on Apple's page.)

| Code | Language (Apple's name) |
|---|---|
| ar-SA | Arabic |
| bn-BD | Bangla |
| ca | Catalan |
| cs | Czech |
| da | Danish |
| de-DE | German |
| el | Greek |
| en-AU | English (Australia) |
| en-CA | English (Canada) |
| en-GB | English (U.K.) |
| en-US | English (U.S.) |
| es-ES | Spanish (Spain) |
| es-MX | Spanish (Mexico) |
| fi | Finnish |
| fr-CA | French (Canada) |
| fr-FR | French |
| gu-IN | Gujarati |
| he | Hebrew |
| hi | Hindi |
| hr | Croatian |
| hu | Hungarian |
| id | Indonesian |
| it | Italian |
| ja | Japanese |
| kn-IN | Kannada |
| ko | Korean |
| ml-IN | Malayalam |
| mr-IN | Marathi |
| ms | Malay |
| nl-NL | Dutch |
| no | Norwegian |
| or-IN | Odia |
| pa-IN | Punjabi |
| pl | Polish |
| pt-BR | Portuguese (Brazil) |
| pt-PT | Portuguese (Portugal) |
| ro | Romanian |
| ru | Russian |
| sk | Slovak |
| sl-SI | Slovenian |
| sv | Swedish |
| ta-IN | Tamil |
| te-IN | Telugu |
| th | Thai |
| tr | Turkish |
| uk | Ukrainian |
| ur-PK | Urdu |
| vi | Vietnamese |
| zh-Hans | Chinese (Simplified) |
| zh-Hant | Chinese (Traditional) |

Apple's list: https://developer.apple.com/help/app-store-connect/reference/app-information/app-store-localizations
(fetched via summarizing WebFetch; page lists language NAMES only, no codes, and does not flag which are new).
Names there: the 50 above, one-to-one. Codes in the table are fastlane's, not Apple's page.

Recently added (inferred, not stated by Apple): Bangla, Gujarati, Kannada, Malayalam, Marathi, Odia,
Punjabi, Tamil, Telugu, Slovenian, Urdu = exactly the 11 in fastlane PR #29959 (May 2026). fastlane
master includes them; older fastlane (before that PR) will reject these folders.
Mapping caveat: spaceship's `languageMapping.json` (itc_locale) was aligned in the same PR; older
legacy names (cmn-Hans etc.) exist only for deprecated name-based input, not deliver folders.
Other related lists fastlane says should be kept in sync: produce/lib/produce/available_default_languages.rb,
spaceship/lib/assets/languageMapping.json.

Note: names like `zh-Hans` / `no` are accepted case-insensitively. Plain `de`, `es`, `fr`, `pt`, `en`, `ja-JP`,
`zh-CN` are NOT accepted as deliver folders. A previous (pre-2015) legacy list `ALL_LANGUAGES_LEGACY` is not used for folder matching.

## 2. Google Play (fastlane supply)

IMPORTANT finding: `supply` does NOT validate against a code list. It uploads whatever directories exist
under `metadata/android/` (`Uploader#all_languages` = every non-dot subdirectory name,
https://github.com/fastlane/fastlane/blob/master/supply/lib/supply/uploader.rb) and passes the folder name
straight to the Google Play API. So the valid folder names are the Play API / Play Console codes, hyphenated
(e.g. `en-US`, `iw-IL`). `Supply::Languages::ALL_LANGUAGES` exists (below) but a search of the repo showed
no consumer in the files I checked (client.rb, uploader.rb, options.rb, supply.rb); it is also stale and uses
underscores. Use the Play Console list, not this constant, as the authority.

- Constant: https://github.com/fastlane/fastlane/blob/master/supply/lib/supply/languages.rb
  (last changed 2021-04-22, still same at master @ fb7e738d0e8dc20fde488287f593dc40657163db). Comment in file:
  "Add your own text translations ... See available languages => replace `-` with `_`" (source: Play help 3125566).

Exact constant (as in source, underscores):

```ruby
ALL_LANGUAGES = %w[
  af am ar az_AZ be bg bn_BD ca cs_CZ da_DK de_DE el_GR en_AU en_CA en_GB en_IN en_SG en_US en_ZA
  es_419 es_ES es_US et eu_ES fa fi_FI fil fr_CA fr_FR gl_ES hi_IN hr hu_HU hy_AM id is_IS it_IT
  iw_IL ja_JP ka_GE km_KH kn_IN ko_KR ky_KG lo_LA lt lv mk_MK ml_IN mn_MN mr_IN ms ms_MY my_MM
  ne_NP nl_NL no_NO pl_PL pt_BR pt_PT rm ro ru_RU si_LK sk sl sr sv_SE sw ta_IN te_IN th tr_TR
  uk vi zh_CN zh_HK zh_TW zu
]
```
(In the source this is one code per line; 79 entries. Whitespace condensed here only.)

Google Play Console help, "Translate & localize your app" / available languages (store listing):
https://support.google.com/googleplay/android-developer/answer/3125566?hl=en
(fetched 2026-10-01 via summarizing WebFetch; hyphenated codes as shown there). Use these for
`metadata/android/<code>/`:

| Code | Language | Code | Language |
|---|---|---|---|
| af | Afrikaans | sq | Albanian |
| am | Amharic | ar | Arabic |
| hy-AM | Armenian | az-AZ | Azerbaijani |
| bn-BD | Bangla | eu-ES | Basque |
| be | Belarusian | bg | Bulgarian |
| my-MM | Burmese | ca | Catalan |
| zh-HK | Chinese (Hong Kong) | zh-CN | Chinese (Simplified) |
| zh-TW | Chinese (Traditional) | hr | Croatian |
| cs-CZ | Czech | da-DK | Danish |
| nl-NL | Dutch | en-AU | English (Australia) |
| en-CA | English (Canada) | en-US | English (US) |
| en-GB | English (UK) | en-IN | English (India) |
| en-SG | English (Singapore) | en-ZA | English (South Africa) |
| et | Estonian | fil | Filipino |
| fi-FI | Finnish | fr-CA | French (Canada) |
| fr-FR | French (France) | gl-ES | Galician |
| ka-GE | Georgian | de-DE | German |
| el-GR | Greek | gu | Gujarati |
| iw-IL | Hebrew | hi-IN | Hindi |
| hu-HU | Hungarian | is-IS | Icelandic |
| id | Indonesian | it-IT | Italian |
| ja-JP | Japanese | kn-IN | Kannada |
| kk | Kazakh | km-KH | Khmer |
| ko-KR | Korean | ky-KG | Kyrgyz |
| lo-LA | Lao | lv | Latvian |
| lt | Lithuanian | mk-MK | Macedonian |
| ms-MY | Malay (Malaysia) | ms | Malay |
| ml-IN | Malayalam | mr-IN | Marathi |
| mn-MN | Mongolian | ne-NP | Nepali |
| no-NO | Norwegian | fa | Persian |
| fa-AE | Persian (UAE) | fa-AF | Persian (Afghanistan) |
| fa-IR | Persian (Iran) | pl-PL | Polish |
| pt-BR | Portuguese (Brazil) | pt-PT | Portuguese (Portugal) |
| pa | Punjabi | ro | Romanian |
| rm | Romansh | ru-RU | Russian |
| sr | Serbian | si-LK | Sinhala |
| sk | Slovak | sl | Slovenian |
| es-419 | Spanish (Latin America) | es-ES | Spanish (Spain) |
| es-US | Spanish (US) | sw | Swahili |
| sv-SE | Swedish | ta-IN | Tamil |
| te-IN | Telugu | th | Thai |
| tr-TR | Turkish | uk | Ukrainian |
| ur | Urdu | vi | Vietnamese |

Not in the Play help list but in fastlane's stale constant: `zu` (Zulu). In Play help but not in the constant:
`sq`, `gu`, `kk`, `pa`, `ur`, `fa-AE`, `fa-AF`, `fa-IR`.
Caveat: Play help page is JS-rendered and my fetch was summarized by a model; spot-check high-value codes in the
Play Console UI before shipping. Codes could not be cross-checked against the Google Play Developer API docs here.

Non-BCP-47 / differing codes:
- `iw-IL` = Hebrew (legacy ISO 639 code; BCP-47 / Apple use `he`).
- `no-NO` = Norwegian (Apple: `no`; BCP-47 would be `nb`/`no`).
- `fil` = Filipino (BCP-47 `fil`, fine; Apple has no Filipino).
- `es-419` = Latin American Spanish (valid BCP-47; Apple has es-MX instead).
- `zh-CN`/`zh-TW`/`zh-HK` use region, not script (Apple: zh-Hans/zh-Hant).
- Mixed bare/regional style: Play uses bare `hr`, `ro`, `uk`, `vi`, `id`, `th` but `cs-CZ`, `pl-PL`, `ja-JP`, etc.
- `id` (Indonesian; legacy `in` not used), `ms` and `ms-MY` both exist.

## 3. Cross-store mapping notes for a screenshot exporter
- Apple uses script subtags for Chinese, Play uses region: zh-Hans -> zh-CN, zh-Hant -> zh-TW (or zh-HK).
- he (Apple) -> iw-IL (Play). no (Apple) -> no-NO (Play).
- es-MX (Apple) vs es-419 / es-US (Play). pt-BR/pt-PT both stores.
- Apple has no Filipino, Serbian, Swahili etc.; Play has no es-MX, ar-SA (just `ar`).
- Play has 80+ codes, Apple 50.
