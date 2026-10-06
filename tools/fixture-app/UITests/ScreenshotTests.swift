import XCTest

// What a team's screenshot tests look like, with no shotfleet code in them. shotfleet sets the language on the simulator.

/// XCTAttachment screenshots: shotfleet reads them from the result bundle ([capture] screenshots = "attachments").
final class ScreenshotTests: XCTestCase {
    func testScreenshots() {
        let app = XCUIApplication()
        app.launch()
        snap("01_welcome")
        app.buttons.firstMatch.tap()  // the one button: Next, in whatever language
        snap("02_settings")
    }

    private func snap(_ name: String) {
        let a = XCTAttachment(screenshot: XCUIScreen.main.screenshot())
        a.name = name
        a.lifetime = .keepAlways  // without it a passing test keeps no attachment
        add(a)
    }
}

/// Writes PNGs the way fastlane's SnapshotHelper does: <simulator name>-<name>.png in the Mac user's fastlane cache folder,
/// and only if that folder exists ([capture] screenshots = "fastlane").
final class SnapshotStyleTests: XCTestCase {
    func testScreenshots() throws {
        let app = XCUIApplication()
        app.launch()
        try snapshot("01_welcome")
        app.buttons.firstMatch.tap()
        try snapshot("02_settings")
    }

    private func snapshot(_ name: String) throws {
        let env = ProcessInfo.processInfo.environment
        let home = try XCTUnwrap(env["SIMULATOR_HOST_HOME"]), device = try XCTUnwrap(env["SIMULATOR_DEVICE_NAME"])
        let folder = URL(fileURLWithPath: home).appendingPathComponent("Library/Caches/tools.fastlane/screenshots")
        guard FileManager.default.fileExists(atPath: folder.path) else { print("Problem writing screenshot: no \(folder.path)"); return }  // SnapshotHelper fails silently too
        try XCUIScreen.main.screenshot().pngRepresentation.write(to: folder.appendingPathComponent("\(device)-\(name).png"))
    }
}

/// The mistake shotfleet must catch: an attachment without .keepAlways is dropped when the test passes, so nothing is saved.
final class NoKeepTests: XCTestCase {
    func testScreenshots() {
        let app = XCUIApplication()
        app.launch()
        add(XCTAttachment(screenshot: XCUIScreen.main.screenshot()))
    }
}
