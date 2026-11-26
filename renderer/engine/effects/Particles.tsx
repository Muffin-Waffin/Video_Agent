import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { ParticleKind, Vec3 } from "../types";

export interface ParticlesProps {
  kind: ParticleKind;
  position?: Vec3;
  count?: number;
  spread?: number;
  color?: string;
}

const DEFAULT_COLORS: Record<ParticleKind, string> = {
  smoke: "#ADB5BD",
  fire: "#FF5400",
  explosion: "#FF9E00",
  glow: "#FFD166",
  sparkle: "#FFFFFF",
  rain: "#90E0EF",
};

export const Particles: React.FC<ParticlesProps> = ({
  kind,
  position = [0, 0, 0],
  count = 16,
  spread = 1.5,
  color,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const particleColor = color ?? DEFAULT_COLORS[kind] ?? "#FFFFFF";

  const items = Array.from({ length: count }, (_, i) => {
    const seed = (i * 1.6180339) % 1;
    const angle = seed * Math.PI * 2;
    const radius = ((i % 5) / 5) * spread;
    const speed = kind === "rain" ? -3.0 : kind === "explosion" ? 2.5 : 1.0;
    const cycle = (t * Math.abs(speed) + seed) % 1;

    const x = Math.cos(angle) * radius * (kind === "explosion" ? cycle * 2 : 1);
    const y = kind === "rain" ? (1 - cycle) * spread * 2 : cycle * spread;
    const z = Math.sin(angle) * radius * (kind === "explosion" ? cycle * 2 : 1);
    const size = kind === "glow" ? 0.14 : 0.09 * (1 - cycle * 0.5);

    return { x, y, z, size, key: i };
  });

  return (
    <group position={position}>
      {items.map((p) => (
        <mesh key={p.key} position={[p.x, p.y, p.z]}>
          <sphereGeometry args={[Math.max(0.02, p.size), 8, 8]} />
          <meshBasicMaterial color={particleColor} transparent opacity={0.75} />
        </mesh>
      ))}
    </group>
  );
};
