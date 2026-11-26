import React from "react";
import { ThreeCanvas } from "@remotion/three";
import { useVideoConfig } from "remotion";
import { BackgroundPreset, TerrainPreset } from "../types";

export interface EnvironmentProps {
  background?: BackgroundPreset;
  terrain?: TerrainPreset;
  fogDensity?: number;
  ambientIntensity?: number;
  children?: React.ReactNode;
}

const SKY_COLORS: Record<BackgroundPreset, string> = {
  day: "#87CEEB",
  sunset: "#FF8C61",
  night: "#0D1B2A",
  overcast: "#9EABB8",
  studio: "#1E1E24",
};

const TERRAIN_COLORS: Record<Exclude<TerrainPreset, "none">, string> = {
  grass: "#4F772D",
  sand: "#E6CCB2",
  stone: "#6C757D",
  snow: "#F8F9FA",
};

export const Environment: React.FC<EnvironmentProps> = ({
  background = "day",
  terrain = "grass",
  fogDensity = 0,
  ambientIntensity = 0.65,
  children,
}) => {
  const { width, height } = useVideoConfig();
  const skyColor = SKY_COLORS[background] ?? SKY_COLORS.day;

  return (
    <ThreeCanvas
      width={width}
      height={height}
      style={{ backgroundColor: skyColor }}
      camera={{ position: [0, 3, 10], fov: 45 }}
    >
      <color attach="background" args={[skyColor]} />
      {fogDensity > 0 && <fogExp2 attach="fog" args={[skyColor, fogDensity]} />}
      <ambientLight intensity={ambientIntensity} />
      <hemisphereLight args={[skyColor, "#2B2D42", 0.4]} />

      {terrain !== "none" && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
          <planeGeometry args={[120, 120]} />
          <meshStandardMaterial
            color={TERRAIN_COLORS[terrain] ?? TERRAIN_COLORS.grass}
            roughness={0.9}
          />
        </mesh>
      )}

      {children}
    </ThreeCanvas>
  );
};
