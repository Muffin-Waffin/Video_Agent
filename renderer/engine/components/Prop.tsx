import React from "react";
import { Vec3 } from "../types";

export type PropKind =
  | "tree"
  | "rock"
  | "house"
  | "building"
  | "desk"
  | "monitor"
  | "chair"
  | "box";

export interface PropProps {
  kind: PropKind;
  assetId?: string;
  position?: Vec3;
  rotation?: Vec3;
  scale?: number;
  color?: string;
}

export const Prop: React.FC<PropProps> = ({
  kind,
  position = [0, 0, 0],
  rotation = [0, 0, 0],
  scale = 1,
  color,
}) => {
  return (
    <group position={position} rotation={rotation} scale={[scale, scale, scale]}>
      {kind === "tree" && (
        <>
          <mesh position={[0, 0.75, 0]} castShadow>
            <cylinderGeometry args={[0.18, 0.25, 1.5, 8]} />
            <meshStandardMaterial color="#6F4E37" />
          </mesh>
          <mesh position={[0, 2.0, 0]} castShadow>
            <coneGeometry args={[1.0, 1.8, 8]} />
            <meshStandardMaterial color={color ?? "#2D6A4F"} />
          </mesh>
        </>
      )}

      {kind === "rock" && (
        <mesh position={[0, 0.35, 0]} castShadow>
          <dodecahedronGeometry args={[0.5, 0]} />
          <meshStandardMaterial color={color ?? "#7D8597"} roughness={0.95} />
        </mesh>
      )}

      {kind === "house" && (
        <>
          <mesh position={[0, 1.0, 0]} castShadow>
            <boxGeometry args={[2.6, 2.0, 2.2]} />
            <meshStandardMaterial color={color ?? "#E9ECEF"} />
          </mesh>
          <mesh position={[0, 2.5, 0]} rotation={[0, Math.PI / 4, 0]} castShadow>
            <coneGeometry args={[2.1, 1.2, 4]} />
            <meshStandardMaterial color="#9B2226" />
          </mesh>
        </>
      )}

      {kind === "building" && (
        <mesh position={[0, 3.0, 0]} castShadow>
          <boxGeometry args={[3.0, 6.0, 3.0]} />
          <meshStandardMaterial color={color ?? "#495057"} />
        </mesh>
      )}

      {kind === "desk" && (
        <mesh position={[0, 0.4, 0]} castShadow>
          <boxGeometry args={[1.6, 0.8, 0.8]} />
          <meshStandardMaterial color={color ?? "#8D6E63"} />
        </mesh>
      )}

      {kind === "monitor" && (
        <>
          <mesh position={[0, 0.35, 0]} castShadow>
            <boxGeometry args={[0.9, 0.55, 0.06]} />
            <meshStandardMaterial color={color ?? "#1B263B"} emissive="#1D3557" emissiveIntensity={0.35} />
          </mesh>
          <mesh position={[0, 0.05, 0]}>
            <boxGeometry args={[0.12, 0.1, 0.12]} />
            <meshStandardMaterial color="#415A77" />
          </mesh>
        </>
      )}

      {kind === "chair" && (
        <>
          <mesh position={[0, 0.45, 0]} castShadow>
            <boxGeometry args={[0.55, 0.1, 0.55]} />
            <meshStandardMaterial color={color ?? "#343A40"} />
          </mesh>
          <mesh position={[0, 0.8, -0.22]} castShadow>
            <boxGeometry args={[0.55, 0.6, 0.1]} />
            <meshStandardMaterial color={color ?? "#343A40"} />
          </mesh>
        </>
      )}

      {kind === "box" && (
        <mesh position={[0, 0.5, 0]} castShadow>
          <boxGeometry args={[1, 1, 1]} />
          <meshStandardMaterial color={color ?? "#BC6C25"} />
        </mesh>
      )}
    </group>
  );
};
