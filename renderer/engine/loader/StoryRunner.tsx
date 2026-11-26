import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Transitions } from "../effects/Transitions";
import { ShotConfig } from "../types";

export interface StoryRunnerProps {
  storyId: string;
  title: string;
  shots: ShotConfig[];
  renderShot?: (shot: ShotConfig, index: number) => React.ReactNode;
}

export const StoryRunner: React.FC<StoryRunnerProps> = ({
  title,
  shots,
  renderShot,
}) => {
  if (!shots || shots.length === 0) {
    return (
      <AbsoluteFill
        style={{
          backgroundColor: "#111827",
          color: "#F9FAFB",
          justifyContent: "center",
          alignItems: "center",
          fontFamily: "sans-serif",
          fontSize: 42,
        }}
      >
        {title}
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ backgroundColor: "#000000" }}>
      {shots.map((shot, idx) => (
        <Sequence
          key={shot.shot_id}
          from={shot.start_frame}
          durationInFrames={shot.duration_frames}
        >
          <Transitions
            kind={shot.transition ?? "cut"}
            totalFrames={shot.duration_frames}
          >
            {renderShot ? renderShot(shot, idx) : null}
          </Transitions>
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
