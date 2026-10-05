import { Composition } from "remotion";
import { Clip, type ClipData } from "./Clip";
import manifest from "./manifest.json";

// One landscape (1920x1080) and one square (1080x1080) composition per clip in manifest.json (written by ../prep.py).
// The loop is deliberate: every clip uses the same template; edit the template, not one instance.
const clips = manifest.clips as Record<string, ClipData>;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {Object.entries(clips).map(([id, clip]) => (
        <Composition
          key={id}
          id={id}
          component={Clip}
          durationInFrames={clip.total}
          fps={manifest.fps}
          width={1920}
          height={1080}
          defaultProps={{ id, clip, square: false }}
        />
      ))}
      {Object.entries(clips).map(([id, clip]) => (
        <Composition
          key={`${id}-square`}
          id={`${id}-square`}
          component={Clip}
          durationInFrames={clip.total}
          fps={manifest.fps}
          width={1080}
          height={1080}
          defaultProps={{ id, clip, square: true }}
        />
      ))}
    </>
  );
};
