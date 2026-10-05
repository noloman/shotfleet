# Rendered by render-formula.sh from the TESTED tarball; do not edit the copy in the tap by hand.
# shotfleet is closed source: this formula installs the signed, notarized Apple-silicon folder, it builds nothing.
class Shotfleet < Formula
  desc "Localized App Store and Google Play screenshots, checked in every language"
  homepage "https://shotfleet.com"
  url "@URL@"
  version "@VERSION@"
  sha256 "@SHA256@"
  license :cannot_represent

  livecheck do
    url "https://shotfleet.com/download/VERSION"
    regex(/^v?(\d+(?:\.\d+)+)$/i)
  end

  depends_on arch: :arm64
  depends_on macos: :ventura

  def install
    libexec.install Dir["*"]
    bin.install_symlink libexec/"shotfleet"
  end

  def caveats
    <<~EOS
      Next: shotfleet doctor --fix, then shotfleet init in your app's folder.
      Your licence key: shotfleet activate <key> (check is free without one).
    EOS
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/shotfleet --version")
  end
end
