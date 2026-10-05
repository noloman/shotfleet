// vtest <mode> <image.png> : one Vision text request in one configuration; prints JSON {mode, ms, chars, ...}.
// modes: rev2 (revision 2) | <mode>+cancel (cancel() after 5 s) | default | cpu14 (macOS 14+ compute-device API) | cpuold (usesCPUOnly) | fast | fast+cpu14 | devices | langs
// Build: swiftc -target arm64-apple-macos13.0 vtest.swift -o vtest
import CoreML
import CoreText
import Foundation
import Vision

func request(level: VNRequestTextRecognitionLevel, revision: Int? = nil) -> VNRecognizeTextRequest {
    let r = VNRecognizeTextRequest()
    r.recognitionLevel = level
    if let revision { r.revision = revision }
    return r
}

/// CPU only, by the API of the running macOS. false if the request has no CPU device to assign.
@discardableResult func useCPUOnly(_ r: VNRecognizeTextRequest) -> Bool {
    if #available(macOS 14, *) {
        guard let devices = try? r.supportedComputeStageDevices[.main],
              let cpu = devices.first(where: { if case .cpu = $0 { return true } else { return false } }) else { return false }
        r.setComputeDevice(cpu, for: .main)
        return true
    }
    r.usesCPUOnly = true  // macOS 13: the only way (deprecated from macOS 14, hence the branch above)
    return true
}

let mode = CommandLine.arguments[1]
if mode == "langs" {
    for level in [VNRequestTextRecognitionLevel.accurate, .fast] {
        for rev in VNRecognizeTextRequest.supportedRevisions.sorted() {
            let l = (try? request(level: level, revision: rev).supportedRecognitionLanguages()) ?? []
            print("level=\(level == .accurate ? "accurate" : "fast") revision=\(rev) count=\(l.count) \(l.joined(separator: ","))")
        }
    }
    print("defaultRevision=\(VNRecognizeTextRequest.defaultRevision) currentRevision=\(VNRecognizeTextRequest.currentRevision)")
    exit(0)
}
if mode == "devices" {
    if #available(macOS 14, *) {
        for level in [VNRequestTextRecognitionLevel.accurate, .fast] {
            let r = request(level: level)
            let d = (try? r.supportedComputeStageDevices) ?? [:]
            print("level=\(level == .accurate ? "accurate" : "fast") " + d.map { "\($0.key.rawValue): \($0.value)" }.sorted().joined(separator: " | "))
        }
    } else { print("macOS 13: no compute-device API") }
    exit(0)
}
let fast = mode.hasPrefix("fast")
let req = request(level: fast ? .fast : .accurate, revision: mode.hasPrefix("rev2") ? 2 : nil)
// cancel<N>: cancel() the request after N seconds from another thread (does perform return?)
if mode.hasSuffix("+cancel") { DispatchQueue.global().asyncAfter(deadline: .now() + 5) { req.cancel() } }
if mode.hasSuffix("cpu14") { if !useCPUOnly(req) { print("{\"error\":\"no cpu device\"}"); exit(3) } }
if mode == "cpuold" { req.usesCPUOnly = true }
req.automaticallyDetectsLanguage = true
/// "draw:<text>" renders the text in memory (to meet a script the repo has no screenshot of)
func handler(_ arg: String) -> VNImageRequestHandler {
    guard arg.hasPrefix("draw:") else { return VNImageRequestHandler(url: URL(fileURLWithPath: arg)) }
    let ctx = CGContext(data: nil, width: 700, height: 160, bitsPerComponent: 8, bytesPerRow: 0,
                        space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)!
    ctx.setFillColor(CGColor(gray: 1, alpha: 1)); ctx.fill(CGRect(x: 0, y: 0, width: 700, height: 160))
    let font = CTFontCreateWithName("Helvetica" as CFString, 56, nil)
    let line = CTLineCreateWithAttributedString(NSAttributedString(string: String(arg.dropFirst(5)), attributes: [
        NSAttributedString.Key(kCTFontAttributeName as String): font,
        NSAttributedString.Key(kCTForegroundColorAttributeName as String): CGColor(gray: 0, alpha: 1)]))
    ctx.textPosition = CGPoint(x: 20, y: 55); CTLineDraw(line, ctx)
    return VNImageRequestHandler(cgImage: ctx.makeImage()!)
}
let t0 = Date()
do {
    try handler(CommandLine.arguments[2]).perform([req])
    let text = (req.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
    let ms = Int(Date().timeIntervalSince(t0) * 1000)
    let first = String(data: try JSONSerialization.data(withJSONObject: [String(text.prefix(Int(ProcessInfo.processInfo.environment["VT_CHARS"] ?? "60") ?? 60))]), encoding: .utf8)!
    print("{\"mode\":\"\(mode)\",\"ms\":\(ms),\"lines\":\((req.results ?? []).count),\"chars\":\(text.count),\"first\":\(first)}")
} catch {
    print("{\"mode\":\"\(mode)\",\"error\":\"\(error)\"}")
    exit(2)
}
// rebuilt 1791207960
