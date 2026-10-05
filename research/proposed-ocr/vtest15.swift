// vtest15 <default|fast|langs> <image.png> : the macOS 15+ Swift Vision API (RecognizeTextRequest). Build: swiftc -target arm64-apple-macos15.0
import Foundation
import Vision

if #available(macOS 15, *) {
    let arg = CommandLine.arguments[1], image = CommandLine.arguments.count > 2 ? CommandLine.arguments[2] : ""
    var req = RecognizeTextRequest()
    if arg == "langs" {
        for level in [RecognizeTextRequest.RecognitionLevel.accurate, .fast] {
            var r = RecognizeTextRequest(); r.recognitionLevel = level
            let l = r.supportedRecognitionLanguages.map { $0.maximalIdentifier }
            print("\(level) count=\(l.count) \(l.joined(separator: ","))")
        }
        exit(0)
    }
    req.recognitionLevel = arg == "fast" ? .fast : .accurate
    req.automaticallyDetectsLanguage = true
    let t0 = Date()
    do {
        let obs = try await req.perform(on: URL(fileURLWithPath: image))
        let text = obs.compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
        let first = String(data: try JSONSerialization.data(withJSONObject: [String(text.prefix(60))]), encoding: .utf8)!
        print("{\"api\":\"swift15\",\"ms\":\(Int(Date().timeIntervalSince(t0) * 1000)),\"lines\":\(obs.count),\"chars\":\(text.count),\"first\":\(first)}")
    } catch { print("{\"error\":\"\(error)\"}"); exit(2) }
} else { print("needs macOS 15"); exit(4) }
