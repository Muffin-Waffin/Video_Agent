import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { TransitionKind } from "../types";

export interface TransitionsProps {
  kind?: TransitionKind;
  durationFrames?: number;
  totalFrames: number;
  children: React.ReactNode;
}

export const Transitions: React.FC<TransitionsProps> = ({
  kind = "cut",
  durationFrames = 12,
  totalFrames,
  children,
}) => {
  const frame = useCurrentFrame();

  if (kind === "cut") {
    return <AbsoluteFill>{children}</AbsoluteFill>;
  }

  const fadeIn = interpolate(frame, [0, durationFrames], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const fadeOut = interpolate(
    frame,
    [Math.max(0, totalFrames - durationFrames), totalFrames],
    [1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  if (kind === "fade") {
    return (
      <AbsoluteFill style={{ opacity: Math.min(fadeIn, fadeOut) }}>
        {children}
      </AbsoluteFill>
    );
  }

  if (kind === "zoom_in") {
    const scale = interpolate(frame, [0, durationFrames], [1.08, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    });
    return (
      <AbsoluteFill style={{ transform: `scale(${scale})`, opacity: fadeIn }}>
        {children}
      </AbsoluteFill>
    );
  }

  const translateX =
    kind === "wipe_left"
      ? interpolate(frame, [0, durationFrames], [100, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        })
      : interpolate(frame, [0, durationFrames], [-100, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        });

  return (
    <AbsoluteFill style={{ transform: `translateX(${translateX}%)` }}>
      {children}
    </AbsoluteFill>
  );
};
