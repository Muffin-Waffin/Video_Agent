import { interpolate, Easing } from "remotion";
import { Vec3 } from "../types";

export function interpolateVec3(
  frame: number,
  inputRange: [number, number],
  from: Vec3,
  to: Vec3,
  easing: (t: number) => number = Easing.inOut(Easing.ease)
): Vec3 {
  const [start, end] = inputRange;
  if (end <= start) return to;

  return [
    interpolate(frame, [start, end], [from[0], to[0]], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing,
    }),
    interpolate(frame, [start, end], [from[1], to[1]], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing,
    }),
    interpolate(frame, [start, end], [from[2], to[2]], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing,
    }),
  ];
}

export function bobbingOffset(
  frame: number,
  fps: number,
  frequencyHz = 1.5,
  amplitude = 0.05
): number {
  const t = frame / fps;
  return Math.sin(t * Math.PI * 2 * frequencyHz) * amplitude;
}
