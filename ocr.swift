// ocr <image.png> -> {"lang": "de", "chars": 812, "text": "..."}
// Uses Vision text recognition + NaturalLanguage language detection (both built into macOS).
import Foundation
import CoreText
import NaturalLanguage
import Vision

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
if CommandLine.arguments[1] == "--langs" {  // languages this Mac's text recognition can read
    print(String(data: try JSONSerialization.data(withJSONObject: try request.supportedRecognitionLanguages()), encoding: .utf8)!)
    exit(0)
}
if CommandLine.arguments[1] == "--warmup" {  // draw a word in memory and read it: makes macOS compile its model now
    let ctx = CGContext(data: nil, width: 400, height: 120, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(gray: 1, alpha: 1)); ctx.fill(CGRect(x: 0, y: 0, width: 400, height: 120))
    let font = CTFontCreateWithName("Helvetica" as CFString, 64, nil)
    let line = CTLineCreateWithAttributedString(NSAttributedString(string: "Ready", attributes: [
        NSAttributedString.Key(kCTFontAttributeName as String): font,
        NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 0, alpha: 1)]))
    ctx.textPosition = CGPoint(x: 20, y: 35); CTLineDraw(line, ctx)
    try VNImageRequestHandler(cgImage: ctx.makeImage()!).perform([request])
    print((request.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: " "))
    exit(0)
}
let url = URL(fileURLWithPath: CommandLine.arguments[1])
request.automaticallyDetectsLanguage = true
try VNImageRequestHandler(url: url).perform([request])

let observations = request.results ?? []
let text = observations.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
// each line with its height and top edge as fractions of the image (Vision's origin is bottom-left)
let lines: [[String: Any]] = observations.compactMap { o in
    guard let t = o.topCandidates(1).first?.string else { return nil }
    return ["text": t, "h": o.boundingBox.height, "top": 1 - o.boundingBox.maxY]
}
let recognizer = NLLanguageRecognizer()
recognizer.processString(text)
let lang = recognizer.dominantLanguage?.rawValue
let langs = Dictionary(uniqueKeysWithValues:
    recognizer.languageHypotheses(withMaximum: 3).map { ($0.key.rawValue, $0.value) })

// marketing caption: text in the top third at least twice as tall as the typical line (framed store screenshots)
let heights = observations.map { $0.boundingBox.height }.sorted()
let median = heights.isEmpty ? 0 : heights[heights.count / 2]
let caption = observations.filter { $0.boundingBox.height >= 2 * median && 1 - $0.boundingBox.maxY < 0.33 }
    .compactMap { $0.topCandidates(1).first?.string }.joined(separator: " ")
var captionLang: Any = NSNull()
if caption.count >= 8 {
    let r = NLLanguageRecognizer(); r.processString(caption)
    if let (l, p) = r.languageHypotheses(withMaximum: 1).first, p >= 0.8 { captionLang = l.rawValue }
}
let out: [String: Any] = ["lang": lang ?? NSNull(), "langs": langs, "chars": text.count, "text": text, "lines": lines,
                          "caption": caption, "caption_lang": captionLang]
print(String(data: try JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
