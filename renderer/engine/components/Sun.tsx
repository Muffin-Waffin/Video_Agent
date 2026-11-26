import React from "react";
import { Vec3 } from "../types";

export interface SunProps {
  position?: Vec3;
  intensity?: number;
  color?: string;
  radius?: number;
  showOrb?: boolean;
}

export const Sun: React.FC<SunProps> = ({
  position = [10, 15, -10],
  intensity = 1.2,
  color = "#FFF3B0",
  radius = 1.5,
  showOrb = true,
}) => {
  return (
    <group>
      <directionalLight
        position={position}
        intensity={intensity}
        color={color}
        castShadow
      />
      {showOrb && (
        <mesh position={position}>
          <sphereGeometry args={[radius, 24, 24]} />
          <meshBasicMaterial color={color} />
        </mesh>
      )}
    </group>
  );
};
