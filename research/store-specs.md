# Store screenshot specs (fetched 2026-10-01, raw page text, not summaries)

Sources (primary):
- Apple: https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications
- Google: https://support.google.com/googleplay/android-developer/answer/9866151
- fastlane: https://github.com/fastlane/fastlane/blob/master/deliver/lib/deliver/app_screenshot.rb (raw master fetched today)

## 1. App Store (Apple)

General (all classes): "You can upload one to 10 screenshots in .jpeg, .jpg, and .png formats." "Images can't include alpha channels or transparencies."
Not stated on Apple's page: color space, max file size, per-localization minimum beyond "one" -> UNVERIFIED (page silent).
Apple's page has no "6.7"" class: 6.7" sizes (1290x2796) are listed inside 6.9". Apple's page has no 6.7"/6.9" naming conflict.

Format: W x H, listed as portrait / landscape (landscape = swapped).

| Class | Accepted sizes (portrait; landscape is swapped) | Required? / scale-down rule |
|---|---|---|
| iPhone Duo | 1398x2034 (landscape 2034x1398, outer display); 2007x2853 (landscape 2853x2007, inner) | Apple: upload support "will be available later this year" (not yet uploadable) |
| 6.9" | 1260x2736; 1290x2796; 1320x2868 | Required for iPhone, unless 6.5" supplied (see next row) |
| 6.5" | 1284x2778; 1242x2688 | "Required if app runs on iPhone and screenshots for 6.9" display aren't provided". If absent, "scaled screenshots for 6.9" displays are used" |
| 6.3" | 1179x2556; 1206x2622 | Optional; falls back to scaled 6.5" |
| 6.1" | 1170x2532; 1125x2436; 1080x2340 | Optional; falls back to scaled 6.5" |
| 5.5" | 1242x2208 | Optional; falls back to scaled 6.1" |
| 4.7" | 750x1334 | Optional; falls back to scaled 5.5" |
| 4" | 640x1096 (no status bar), 640x1136 (with); landscape 1136x600, 1136x640 | Optional; falls back to scaled 4.7" |
| 3.5" | 640x920, 640x960; landscape 960x600, 960x640 | Optional; falls back to scaled 4" |
| iPad 13" | 2064x2752; 2048x2732 | "Required if app runs on iPad" |
| iPad 12.9" (Pro 2nd gen) | 2048x2732 | Optional; falls back to scaled 13" |
| iPad 11" | 1488x2266; 1668x2420; 1668x2388; 1640x2360 | Optional; falls back to scaled 13" |
| iPad 10.5" | 1668x2224 | Optional; falls back to scaled 12.9" |
| iPad 9.7" | 1536x2008 / 1536x2048; landscape 2048x1496 / 2048x1536; also 768x1004 / 768x1024; landscape 1024x748 / 1024x768 | Optional; falls back to scaled 10.5" |
| Mac | 1280x800, 1440x900, 2560x1600, 2880x1800 ("16:10 aspect ratio"; one of) | "Required for Mac apps" |
| Apple TV | 1920x1080, 3840x2160 | "Required for Apple TV apps" |
| Vision Pro | 3840x2160 | "Required for Apple Vision Pro" |
| Apple Watch | 422x514 (Ultra 4/3); 410x502 (Ultra 2/Ultra); 416x496 (S12/11/10); 396x484 (S9/8/7); 368x448 (S6/5/4, SE 3/2/SE); 312x390 (S3/2/1) | "Required for Apple Watch apps". "You must use the same screenshot size for Apple Watch consistently across all localizations" |

Mac/TV/Vision/Watch sizes are not tagged portrait/landscape by Apple.
The 4", 3.5" and 9.7" sizes with/without status bar are both accepted per Apple's text.
Note: the 6.9"/13" iPad rows only list newer devices; whether these legacy classes (<=5.5", 9.7", 10.5") still accept uploads in the App Store Connect UI is not stated beyond being on the page.

## 2. Google Play

Source page: answer/9866151, "Screenshots" section. All quotes below are verbatim.

- Count: "You can add up to 8 screenshots for each supported device type." Device types: phones, tablets (7-inch and 10-inch), Chromebooks, Android TVs, Wear OS, Android Automotive OS, Android XR.
- To publish: "a minimum of two screenshots across different device types". (Per-type minimum for phone is not stated as a number other than this; UNVERIFIED whether a phone-only listing needs >=2 phone shots.)
- General Requirements (apply to all):
  - "JPEG or 24-bit PNG (no alpha)"
  - "Minimum dimension: 320px"
  - "Maximum dimension: 3840px"
  - "The maximum dimension of your screenshot can't be more than twice as long as the minimum dimension."
- IMPORTANT for 1080x2400 (20:9): 2400 > 2 x 1080 = 2160, so by this wording it is NOT allowed (max ratio 2:1; longest 1080x2160). Phone-specific wording on the page does not override this. Caveat: the Play Console upload UI behaviour was not tested; this is the documented rule.
- Chromebook and tablets (7"/10"): "a minimum of 4 screenshots"; "Upload screenshots between 1,080 and 7,680px"; "Use a 16:9 aspect ratio for landscape and a 9:16 aspect ratio for portrait". (Page lists them together; no separate 7" vs 10" numbers.) Note 7,680 conflicts with the general 3,840 max; page does not reconcile - UNVERIFIED which the Console enforces for tablets.
- Phone: no phone-specific section besides the general rules and the promotion rule below.
- Wear OS (app and watch face): at least one screenshot; 1:1 aspect ratio, minimum 384x384; app interface only, no device frames/extra text/graphics.
- Android TV: "at least one Android TV screenshot" required to publish (plus banner image). No size/ratio stated -> UNVERIFIED.
- Android Automotive OS: required unless app is in a parked category; if provided, "at least 2 portraits (800 px by 1,280 px) and 2 landscape (1,024 px by 768 px)".
- Android XR: "between 4 and 8 screenshots. PNG or JPEG, up to 8 MB each, 8:5 aspect ratio." Recommended 3840x2400, minimum 1920x1200.
- Max file size (non-XR): not stated on the page -> UNVERIFIED. Color space: not stated -> UNVERIFIED.
- Promotion/recommendation eligibility (verbatim):
  - Apps: "at least four screenshots with minimum 1080px resolution. These should be 16:9 for landscape (minimum 1920x1080px) screenshots and 9:16 for portrait screenshots (minimum 1080x1920px)."
  - Games: "at least three 16:9 landscape screenshots (minimum 1920x1080px) or three 9:16 portrait screenshots (minimum 1080x1920px)", depicting in-game experience.
  - So a 20:9 phone shot meets upload limits only if <= 2:1, and does not meet the 16:9 / 9:16 recommendation format regardless.

## 3. fastlane deliver table (master, DEVICE_RESOLUTIONS, copied exactly)

Keys are Spaceship DisplayType constants. Comments in source: APP_IPHONE_67 = "actually 6.9" iPhones"; APP_IPHONE_61 = "actually 6.3""; APP_IPHONE_58 = "actually 6.1""; APP_IPAD_PRO_129 = 12.9"; APP_IPAD_PRO_3GEN_129 = "actually 13" iPads".

```ruby
DisplayType::APP_IPHONE_67 => [[1260, 2736],[2736, 1260],[1290, 2796],[2796, 1290],[1320, 2868],[2868, 1320]],
DisplayType::APP_IPHONE_65 => [[1242, 2688],[2688, 1242],[1284, 2778],[2778, 1284]],
DisplayType::APP_IPHONE_61 => [[1179, 2556],[2556, 1179],[1206, 2622],[2622, 1206]],
DisplayType::APP_IPHONE_58 => [[1170, 2532],[2532, 1170],[1125, 2436],[2436, 1125],[1080, 2340],[2340, 1080]],
DisplayType::APP_IPHONE_55 => [[1242, 2208],[2208, 1242]],
DisplayType::APP_IPHONE_47 => [[750, 1334],[1334, 750]],
DisplayType::APP_IPHONE_40 => [[640, 1096],[640, 1136],[1136, 600],[1136, 640]],
DisplayType::APP_IPHONE_35 => [[640, 920],[640, 960],[960, 600],[960, 640]],
DisplayType::APP_IPAD_97 => [[1024, 748],[1024, 768],[2048, 1496],[2048, 1536],[768, 1004],[768, 1024],[1536, 2008],[1536, 2048]],
DisplayType::APP_IPAD_105 => [[1668, 2224],[2224, 1668]],
DisplayType::APP_IPAD_PRO_3GEN_11 => [[1488, 2266],[2266, 1488],[1668, 2420],[2420, 1668],[1668, 2388],[2388, 1668],[1640, 2360],[2360, 1640]],
DisplayType::APP_IPAD_PRO_129 => [[2048, 2732],[2732, 2048]],
DisplayType::APP_IPAD_PRO_3GEN_129 => [[2048, 2732],[2732, 2048],[2064, 2752],[2752, 2064]],
DisplayType::APP_DESKTOP => [[1280, 800],[1440, 900],[2560, 1600],[2880, 1800]],
DisplayType::APP_WATCH_SERIES_3 => [[312, 390]],
DisplayType::APP_WATCH_SERIES_4 => [[368, 448]],
DisplayType::APP_WATCH_SERIES_7 => [[396, 484]],
DisplayType::APP_WATCH_SERIES_10 => [[416, 496]],
DisplayType::APP_WATCH_ULTRA => [[410, 502],[422, 514]],
DisplayType::APP_APPLE_TV => [[1920, 1080],[3840, 2160]],
DisplayType::APP_APPLE_VISION_PRO => [[3840, 2160]]
```
iMessage variants (folder `.../iMessage/<file>`, path component [-3]) reuse the iPhone/iPad rows (no Mac/Watch/TV/Vision).
Conflicting sizes disambiguated by path string: [2048,2732]/[2732,2048] -> 12.9" 2nd gen if path contains "app_ipad_pro_129" or ("12.9" and "2nd generation"), else 13"; [3840,2160] -> Vision Pro if path contains "vision", else Apple TV. First match in hash order wins otherwise. fastlane does not check alpha, color space, or file size in this file (extension/alpha checks live in AppScreenshotValidator - not fetched, UNVERIFIED).

## 4. Disagreements: Apple page vs fastlane

Per-size comparison: NO numeric disagreement found. Every size on Apple's page for iPhone 6.9", 6.5", 6.3", 6.1", 5.5", 4.7", 4", 3.5", iPad 13", 12.9", 11", 10.5", 9.7", Mac, TV, Vision, Watch appears in fastlane and vice versa.
- 6.9": Apple lists 1260x2736, 1290x2796 AND 1320x2868 (plus landscape). fastlane lists the same three. The App Store accepts all three per Apple; none supersedes another. (1320x2868 is not "the" size; 1260x2736 is valid too.)
- Naming only: fastlane constants are legacy (`67` = 6.9", `61` = 6.3", `58` = 6.1", `PRO_3GEN_129` = 13"). Do not key your linter off the fastlane names.
- Apple-only: iPhone Duo (1398x2034, 2007x2853 + landscapes; Apple says uploads not yet available). Not in fastlane.
- Apple-only: the textual required/optional/fallback rules, formats, 1-10 count, no-alpha. fastlane's table has none of these.
- fastlane-only: iMessage variants, filename-based tie-breaks; coarser watch classes (Series 3/4/7/10/Ultra) vs Apple's device lists (equivalent sizes).
- Apple's 6.9" requirement: 6.9" OR 6.5" must be supplied for iPhone. Apple's 6.5"/6.9" cross-references are slightly inconsistent in direction (6.5" row says 6.9" is scaled; 6.3" and 6.1" say they fall back to 6.5"). Reproduce verbatim in the linter.
