import { loadFont } from "@remotion/fonts";
import { Video } from "@remotion/media";
import { linearTiming, TransitionSeries } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import manifest from "./manifest.json";
import { Subtitles } from "./Subtitles";

loadFont({ family: "Geist Mono", url: staticFile("fonts/geist-mono-latin.woff2"), weight: "100 900" });

export const INK = "#0b1220";
export const PAPER = "#f1f2f4";
export const YEL = "#f5c400";
export const DIM = "#7f93ab";
export const FONT = "'Geist Mono', ui-monospace, monospace";

// Shown on the outro card. These two sentences are on site/public/index.html (prep.py does not check them; keep them in sync).
const PRICE = ["$29 launch price, first 100 buyers", "Then $49 once, per developer."];

type Shot = { lang: string; src: string; w: number; h: number };
export type ClipData = {
  label: string;
  body: number;
  grid: { device: string; items: Shot[] }[];
  gridFrames: number;
  speed: number;
  spedFrom: number;
  spedFrames: number;
  spedReal: number;
  total: number;
};
type Props = { id: string; clip: ClipData; square: boolean };

const Brand: React.FC<{ size: number }> = ({ size }) => (
  <div style={{ display: "flex", alignItems: "center", gap: size * 0.3 }}>
    <Img src={staticFile("favicon.svg")} style={{ width: size * 1.1, height: size * 1.1 }} />
    <span style={{ fontFamily: FONT, fontWeight: 700, fontSize: size, color: PAPER }}>shotfleet</span>
  </div>
);

const Card: React.FC<{ lines: string[]; square: boolean }> = ({ lines, square }) => {
  const frame = useCurrentFrame();
  const s = square ? 0.85 : 1;
  return (
    <AbsoluteFill style={{ backgroundColor: INK, justifyContent: "center", alignItems: "center", gap: 48 * s }}>
      <div
        style={{
          scale: interpolate(frame, [0, 18], [0.92, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <Brand size={104 * s} />
      </div>
      {lines.map((l, i) => (
        <div
          key={l}
          style={{
            fontFamily: FONT,
            fontWeight: i === 0 ? 700 : 400,
            fontSize: (i === 0 ? 56 : 40) * s,
            color: i === 0 ? YEL : PAPER,
            textAlign: "center",
            padding: "0 80px",
            opacity: interpolate(frame, [6 + i * 6, 18 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          }}
        >
          {l}
        </div>
      ))}
    </AbsoluteFill>
  );
};

// The VHS recording (1600x880), already cut and sped up by prep.py. Sped-up stretch gets a yellow badge.
const Terminal: React.FC<Props> = ({ id, clip, square }) => {
  const { fps } = useVideoConfig();
  const w = square ? 1080 : 1440;
  const h = (w * 880) / 1600;
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      {square ? (
        <div style={{ position: "absolute", top: 44, left: 48 }}>
          <Brand size={40} />
        </div>
      ) : null}
      <Video
        src={staticFile(`rec/${id}.mp4`)}
        premountFor={fps}
        muted
        style={{ position: "absolute", width: w, height: h, left: (square ? 1080 : 1920) / 2 - w / 2, top: square ? 130 : 28 }}
      />
      {clip.speed > 1 ? (
        <Sequence from={clip.spedFrom} durationInFrames={clip.spedFrames} premountFor={fps}>
          <div
            style={{
              position: "absolute",
              top: square ? 40 : 44,
              right: square ? 48 : 260,
              backgroundColor: YEL,
              color: INK,
              fontFamily: FONT,
              fontWeight: 700,
              fontSize: square ? 30 : 34,
              padding: "10px 22px",
              borderRadius: 12,
            }}
          >
            ▶▶ sped up {Math.floor(clip.speed)}x
          </div>
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};

// The run's real screenshots: one row per device, one tile per language, staggered in, with a slow push-in.
const Grid: React.FC<Props> = ({ clip, square }) => {
  const frame = useCurrentFrame();
  const W = square ? 1080 : 1920;
  const areaH = square ? 760 : 820;
  const rows = clip.grid.length;
  const label = 44;
  const gap = 20;
  const th = Math.floor((areaH - rows * label - (rows - 1) * gap) / rows);
  let n = 0;
  return (
    <AbsoluteFill
      style={{
        backgroundColor: INK,
        paddingTop: square ? 140 : 40,
        alignItems: "center",
        gap,
      }}
    >
      {square ? (
        <div style={{ position: "absolute", top: 44, left: 48 }}>
          <Brand size={40} />
        </div>
      ) : null}
      <div style={{ display: "flex", flexDirection: "column", gap, scale: interpolate(frame, [0, clip.gridFrames], [1, 1.035]) }}>
        {clip.grid.map((row) => {
          const widths = row.items.map((it) => Math.floor((it.w * th) / it.h));
          const total = widths.reduce((a, b) => a + b, 0) + gap * (row.items.length - 1);
          const k = Math.min(1, (W - 80) / total);
          return (
            <div key={row.device} style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
              <div style={{ fontFamily: FONT, fontSize: 26, color: DIM, height: label }}>{row.device}</div>
              <div style={{ display: "flex", gap: gap * k }}>
                {row.items.map((it, i) => {
                  const start = 4 + 3 * n++;
                  return (
                    <div key={it.lang} style={{ position: "relative" }}>
                      <Img
                        src={staticFile(it.src)}
                        style={{
                          width: widths[i] * k,
                          height: th * k,
                          borderRadius: 14 * k,
                          opacity: interpolate(frame, [start, start + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                          translate: interpolate(frame, [start, start + 14], ["0px 24px", "0px 0px"], {
                            extrapolateLeft: "clamp",
                            extrapolateRight: "clamp",
                            easing: Easing.bezier(0.16, 1, 0.3, 1),
                          }),
                        }}
                      />
                      <div
                        style={{
                          position: "absolute",
                          top: 8,
                          left: 8,
                          backgroundColor: INK,
                          color: YEL,
                          fontFamily: FONT,
                          fontWeight: 700,
                          fontSize: 24,
                          padding: "2px 10px",
                          borderRadius: 8,
                          opacity: interpolate(frame, [start + 6, start + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
                        }}
                      >
                        {it.lang}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const Clip: React.FC<Props> = (props) => {
  const { fps } = useVideoConfig();
  const { clip, square, id } = props;
  const t = linearTiming({ durationInFrames: manifest.fade });
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      <TransitionSeries>
        <TransitionSeries.Sequence durationInFrames={manifest.intro} premountFor={fps}>
          <Card lines={[clip.label]} square={square} />
        </TransitionSeries.Sequence>
        <TransitionSeries.Transition presentation={fade()} timing={t} />
        <TransitionSeries.Sequence durationInFrames={clip.body} premountFor={fps}>
          <Terminal {...props} />
        </TransitionSeries.Sequence>
        {clip.gridFrames ? <TransitionSeries.Transition presentation={fade()} timing={t} /> : null}
        {clip.gridFrames ? (
          <TransitionSeries.Sequence durationInFrames={clip.gridFrames} premountFor={fps}>
            <Grid {...props} />
          </TransitionSeries.Sequence>
        ) : null}
        <TransitionSeries.Transition presentation={fade()} timing={t} />
        <TransitionSeries.Sequence durationInFrames={manifest.outro} premountFor={fps}>
          <Card lines={["shotfleet.com", ...PRICE]} square={square} />
        </TransitionSeries.Sequence>
      </TransitionSeries>
      <Subtitles src={`srt/${id}.srt`} square={square} />
    </AbsoluteFill>
  );
};
