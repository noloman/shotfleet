// render <jobs.json>: [{"out": "x.png", "lines": ["...", ...]}] -> phone-sized PNGs of those lines (system fonts, natural direction)
import AppKit
struct Job: Decodable { let out: String; let lines: [String] }
let jobs = try JSONDecoder().decode([Job].self, from: Data(contentsOf: URL(fileURLWithPath: CommandLine.arguments[1])))
DispatchQueue.concurrentPerform(iterations: jobs.count) { i in
    let job = jobs[i]
    let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: 1080, pixelsHigh: 1920, bitsPerSample: 8, samplesPerPixel: 4,
                               hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    let ctx = NSGraphicsContext(bitmapImageRep: rep)!
    NSGraphicsContext.saveGraphicsState(); NSGraphicsContext.current = ctx
    NSColor.white.setFill(); NSRect(x: 0, y: 0, width: 1080, height: 1920).fill()
    let style = NSMutableParagraphStyle(); style.alignment = .natural; style.baseWritingDirection = .natural
    var y = 1780.0
    for (n, line) in job.lines.enumerated() {
        let font = n == 0 ? NSFont.boldSystemFont(ofSize: 64) : NSFont.systemFont(ofSize: 46)
        let s = NSAttributedString(string: line, attributes: [.font: font, .foregroundColor: NSColor.black, .paragraphStyle: style])
        let h = s.boundingRect(with: NSSize(width: 960, height: 400), options: [.usesLineFragmentOrigin]).height
        y -= h + 40
        s.draw(with: NSRect(x: 60, y: y, width: 960, height: h + 10), options: [.usesLineFragmentOrigin])
    }
    NSGraphicsContext.restoreGraphicsState()
    try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: job.out))
}
