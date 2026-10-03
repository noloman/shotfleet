import SwiftUI

// A tiny two-screen app with strings in five languages: shotfleet's end-to-end test fixture (tools/fixture-app/build.sh).
@main
struct FixtureApp: App {
    var body: some Scene { WindowGroup { RootView() } }
}

struct RootView: View {
    @State private var onSettings = false
    var body: some View {
        VStack(spacing: 28) {
            Spacer()
            Image(systemName: onSettings ? "gearshape.fill" : "sailboat.fill").font(.system(size: 72)).foregroundStyle(.blue)
            Text(onSettings ? "Settings" : "Welcome").font(.largeTitle.bold())
            Text(onSettings ? "Choose how the app looks and sounds." : "Your screenshots, in every language.")
                .font(.title3).multilineTextAlignment(.center).foregroundStyle(.secondary).padding(.horizontal, 32)
            Button(onSettings ? "Done" : "Next") { onSettings.toggle() }
                .buttonStyle(.borderedProminent).controlSize(.large)
            Spacer()
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemBackground))
    }
}
