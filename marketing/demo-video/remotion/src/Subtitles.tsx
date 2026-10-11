import { parseSrt, type Caption } from "@remotion/captions";
import { useCallback, useEffect, useState } from "react";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame, useDelayRender, useVideoConfig } from "remotion";
import { FONT } from "./Clip";

// Line-timed subtitles from public/srt/<clip>.srt (copied there by prep.py from ../clips/, which checks the length rules):
// white on a dark translucent box, bottom centre, fading and rising in over 5 frames.
export const Subtitles: React.FC<{ src: string; square: boolean }> = ({ src, square }) => {
  const [captions, setCaptions] = useState<Caption[] | null>(null);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => delayRender());
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const load = useCallback(async () => {
    try {
      const res = await fetch(staticFile(src));
      setCaptions(res.ok ? parseSrt({ input: await res.text() }).captions : []);
      continueRender(handle);
    } catch (e) {
      cancelRender(e);
    }
  }, [src, continueRender, cancelRender, handle]);

  useEffect(() => {
    load();
  }, [load]);

  const ms = (frame / fps) * 1000;
  const cue = captions?.find((c) => c.startMs <= ms && ms < c.endMs);
  if (!cue) return null;
  const local = ((ms - cue.startMs) / 1000) * fps;
  const left = ((cue.endMs - ms) / 1000) * fps;
  const k = Math.min(interpolate(local, [0, 5], [0, 1], { extrapolateRight: "clamp" }), interpolate(left, [0, 4], [0, 1], { extrapolateRight: "clamp" }));
  return (
    <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: square ? 44 : 40 }}>
      <div
        style={{
          backgroundColor: "rgba(0, 0, 0, 0.78)",
          color: "#ffffff",
          fontFamily: FONT,
          fontWeight: 600,
          fontSize: square ? 36 : 44,
          lineHeight: 1.3,
          padding: square ? "12px 24px" : "14px 30px",
          borderRadius: 14,
          textAlign: "center",
          whiteSpace: "pre",
          opacity: k,
          translate: `0px ${(1 - k) * 12}px`,
        }}
      >
        {cue.text}
      </div>
    </AbsoluteFill>
  );
};
