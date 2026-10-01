// ocr <image.png> -> {"lang": "de", "chars": 812, "text": "..."}
// Uses Vision text recognition + NaturalLanguage language detection (both built into macOS).
import Foundation
import NaturalLanguage
import Vision

let request = VNRecognizeTextRequest()
request.recognitionLevel = .accurate
if CommandLine.arguments[1] == "--langs" {  // languages this Mac's text recognition can read
    print(String(data: try JSONSerialization.data(withJSONObject: try request.supportedRecognitionLanguages()), encoding: .utf8)!)
    exit(0)
}
let url = URL(fileURLWithPath: CommandLine.arguments[1])
request.automaticallyDetectsLanguage = true
try VNImageRequestHandler(url: url).perform([request])

let text = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
let recognizer = NLLanguageRecognizer()
recognizer.processString(text)
let lang = recognizer.dominantLanguage?.rawValue
let langs = Dictionary(uniqueKeysWithValues:
    recognizer.languageHypotheses(withMaximum: 3).map { ($0.key.rawValue, $0.value) })

let out: [String: Any] = ["lang": lang ?? NSNull(), "langs": langs, "chars": text.count, "text": text]
print(String(data: try JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
