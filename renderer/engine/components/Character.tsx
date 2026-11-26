import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { computeCharacterPose } from "../animations/character";
import { CharacterAnimation, CharacterVariant, Vec3 } from "../types";

export interface CharacterProps {
  model?: CharacterVariant;
  position?: Vec3;
  rotation?: Vec3;
  scale?: number;
  animation?: CharacterAnimation;
  shirtColor?: string;
  pantsColor?: string;
  skinColor?: string;
}

const VARIANT_COLORS: Record<CharacterVariant, { shirt: string; pants: string }> = {
  default_human: { shirt: "#3A86FF", pants: "#2B2D42" },
  casual: { shirt: "#FB5607", pants: "#3D5A80" },
  formal: { shirt: "#1D3557", pants: "#111111" },
  worker: { shirt: "#FFB703", pants: "#4A4E69" },
  explorer: { shirt: "#386641", pants: "#6C584C" },
};

export const Character: React.FC<CharacterProps> = ({
  model = "default_human",
  position = [0, 0, 0],
  rotation = [0, 0, 0],
  scale = 1,
  animation = "idle",
  shirtColor,
  pantsColor,
  skinColor = "#F4C29F",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pose = computeCharacterPose(animation, frame, fps);
  const palette = VARIANT_COLORS[model] ?? VARIANT_COLORS.default_human;

  return (
    <group
      position={[position[0], position[1] + pose.bodyYOffset, position[2]]}
      rotation={rotation}
      scale={[scale, scale, scale]}
    >
      {/* Torso */}
      <group rotation={[pose.bodyTiltX, 0, 0]}>
        <mesh position={[0, 1.05, 0]} castShadow>
          <boxGeometry args={[0.5, 0.7, 0.28]} />
          <meshStandardMaterial color={shirtColor ?? palette.shirt} />
        </mesh>

        {/* Head */}
        <mesh position={[0, 1.62, 0]} rotation={[pose.headNodX, 0, 0]} castShadow>
          <sphereGeometry args={[0.2, 16, 16]} />
          <meshStandardMaterial color={skinColor} />
        </mesh>

        {/* Left Arm */}
        <group position={[-0.35, 1.32, 0]} rotation={[pose.leftArmX, 0, 0]}>
          <mesh position={[0, -0.25, 0]} castShadow>
            <boxGeometry args={[0.15, 0.55, 0.15]} />
            <meshStandardMaterial color={shirtColor ?? palette.shirt} />
          </mesh>
        </group>

        {/* Right Arm */}
        <group position={[0.35, 1.32, 0]} rotation={[pose.rightArmX, 0, 0]}>
          <mesh position={[0, -0.25, 0]} castShadow>
            <boxGeometry args={[0.15, 0.55, 0.15]} />
            <meshStandardMaterial color={shirtColor ?? palette.shirt} />
          </mesh>
        </group>
      </group>

      {/* Left Leg */}
      <group position={[-0.14, 0.7, 0]} rotation={[pose.leftLegX, 0, 0]}>
        <mesh position={[0, -0.35, 0]} castShadow>
          <boxGeometry args={[0.18, 0.7, 0.18]} />
          <meshStandardMaterial color={pantsColor ?? palette.pants} />
        </mesh>
      </group>

      {/* Right Leg */}
      <group position={[0.14, 0.7, 0]} rotation={[pose.rightLegX, 0, 0]}>
        <mesh position={[0, -0.35, 0]} castShadow>
          <boxGeometry args={[0.18, 0.7, 0.18]} />
          <meshStandardMaterial color={pantsColor ?? palette.pants} />
        </mesh>
      </group>
    </group>
  );
};
