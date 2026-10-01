// Builds public/og.png (1200x630 link preview) from the proof-strip screenshots.
import AppKit

let W = 1200.0, H = 630.0
let img = NSImage(size: NSSize(width: W, height: H))
img.lockFocus()
NSColor.white.setFill(); NSRect(x: 0, y: 0, width: W, height: H).fill()

let ink = NSColor(srgbRed: 0.114, green: 0.114, blue: 0.122, alpha: 1)
let amber = NSColor(srgbRed: 0.0, green: 0.4, blue: 0.8, alpha: 1)
let soft = NSColor(srgbRed: 0.431, green: 0.431, blue: 0.451, alpha: 1)
func draw(_ s: String, _ size: CGFloat, _ weight: NSFont.Weight, _ color: NSColor, _ rect: NSRect) {
    let p = NSMutableParagraphStyle(); p.lineSpacing = 4
    (s as NSString).draw(in: rect, withAttributes: [.font: NSFont.systemFont(ofSize: size, weight: weight), .foregroundColor: color, .paragraphStyle: p])
}
draw("shotfleet", 30, .semibold, amber, NSRect(x: 64, y: H - 100, width: 600, height: 44))
draw("Store screenshots in every language\nyour app ships. Checked.", 50, .bold, ink, NSRect(x: 64, y: H - 250, width: 1100, height: 130))

let locales = ["ja", "fr", "ar", "ko", "ru", "es"]
let tw = 160.0, gap = 18.0, top = 320.0
for (i, lp) in locales.enumerated() {
    guard let shot = NSImage(contentsOfFile: "public/img/train_\(lp).jpg") else { continue }
    let x = 64 + Double(i) * (tw + gap)
    let th = tw * shot.size.height / shot.size.width
    let rect = NSRect(x: x, y: H - top - th, width: tw, height: th)
    NSGraphicsContext.saveGraphicsState()
    NSBezierPath(roundedRect: rect, xRadius: 10, yRadius: 10).addClip()
    shot.draw(in: rect)
    NSGraphicsContext.restoreGraphicsState()
    NSColor(srgbRed: 0.898, green: 0.898, blue: 0.918, alpha: 1).setStroke()
    let border = NSBezierPath(roundedRect: rect, xRadius: 10, yRadius: 10); border.lineWidth = 1.5; border.stroke()
    draw(lp, 22, .medium, soft, NSRect(x: x + 2, y: H - top + 8, width: tw, height: 30))
}
img.unlockFocus()
let rep = NSBitmapImageRep(data: img.tiffRepresentation!)!
try! rep.representation(using: .png, properties: [:])!.write(to: URL(fileURLWithPath: "public/og.png"))
