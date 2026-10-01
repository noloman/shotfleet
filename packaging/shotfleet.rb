# Homebrew formula for noloman/homebrew-shotfleet (Formula/shotfleet.rb). release.sh fills in version and sha256.
class Shotfleet < Formula
  desc "Localized App Store and Google Play screenshots from one Maestro flow, checked"
  homepage "https://shotfleet.manulorenzop.workers.dev"
  url "https://github.com/noloman/shotfleet-releases/releases/download/v@VERSION@/shotfleet-@VERSION@-macos-arm64.tar.gz"
  sha256 "@SHA256@"
  version "@VERSION@"

  depends_on arch: :arm64
  depends_on :macos

  def install
    bin.install "shotfleet"
  end

  def caveats
    <<~EOS
      `shotfleet check` is free. `run` and `export` need a licence:
        shotfleet activate <key>
      shotfleet drives Maestro (https://maestro.mobile.dev), Xcode and the Android SDK; `shotfleet doctor` checks them.
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/shotfleet --version")
  end
end
