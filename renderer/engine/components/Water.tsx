import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Vec3, WaterStyle } from "../types";

export interface WaterProps {
  position?: Vec3;
  width?: number;
  depth?: number;
  style?: WaterStyle;
  color?: string;
  opacity?: number;
}

export const Water: React.FC<WaterProps> = ({
  position = [0, 0.02, -5],
  width = 20,
  depth = 8,
  style = "calm",
  color = "#219EBC",
  opacity = 0.82,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;

  const waveY =
    style === "calm"
      ? Math.sin(t * 1.2) * 0.015
      : style === "rippling"
      ? Math.sin(t * 3.0) * 0.04
      : Math.sin(t * 4.5) * 0.05;

  return (
    <mesh
      position={[position[0], position[1] + waveY, position[2]]}
      rotation={[-Math.PI / 2, 0, 0]}
    >
      <planeGeometry args={[width, depth, 16, 16]} />
      <meshStandardMaterial
        color={color}
        transparent
        opacity={opacity}
        roughness={0.15}
        metalness={0.2}
      />
    </mesh>
  );
};
