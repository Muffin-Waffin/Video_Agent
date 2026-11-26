import { CharacterAnimation } from "../types";

export interface CharacterPose {
  bodyYOffset: number;
  bodyTiltX: number;
  leftArmX: number;
  rightArmX: number;
  leftLegX: number;
  rightLegX: number;
  headNodX: number;
}

export function computeCharacterPose(
  animation: CharacterAnimation,
  frame: number,
  fps: number
): CharacterPose {
  const t = frame / fps;

  switch (animation) {
    case "walk": {
      const cycle = t * Math.PI * 3.2;
      return {
        bodyYOffset: Math.abs(Math.sin(cycle)) * 0.06,
        bodyTiltX: 0.06,
        leftArmX: Math.sin(cycle) * 0.45,
        rightArmX: -Math.sin(cycle) * 0.45,
        leftLegX: -Math.sin(cycle) * 0.55,
        rightLegX: Math.sin(cycle) * 0.55,
        headNodX: Math.sin(cycle * 2) * 0.03,
      };
    }
    case "run": {
      const cycle = t * Math.PI * 6.0;
      return {
        bodyYOffset: Math.abs(Math.sin(cycle)) * 0.12,
        bodyTiltX: 0.18,
        leftArmX: Math.sin(cycle) * 0.85,
        rightArmX: -Math.sin(cycle) * 0.85,
        leftLegX: -Math.sin(cycle) * 0.9,
        rightLegX: Math.sin(cycle) * 0.9,
        headNodX: Math.sin(cycle * 2) * 0.05,
      };
    }
    case "interact": {
      const cycle = t * Math.PI * 2.5;
      return {
        bodyYOffset: 0,
        bodyTiltX: 0.12,
        leftArmX: -0.35,
        rightArmX: -0.8 + Math.sin(cycle) * 0.25,
        leftLegX: 0,
        rightLegX: 0,
        headNodX: 0.1,
      };
    }
    case "talk": {
      const cycle = t * Math.PI * 3.0;
      return {
        bodyYOffset: Math.sin(cycle * 0.5) * 0.015,
        bodyTiltX: 0,
        leftArmX: -0.2 + Math.sin(cycle) * 0.15,
        rightArmX: -0.25 - Math.cos(cycle) * 0.18,
        leftLegX: 0,
        rightLegX: 0,
        headNodX: Math.sin(cycle) * 0.08,
      };
    }
    case "wave": {
      const cycle = t * Math.PI * 4.0;
      return {
        bodyYOffset: 0,
        bodyTiltX: 0,
        leftArmX: 0,
        rightArmX: -2.4 + Math.sin(cycle) * 0.35,
        leftLegX: 0,
        rightLegX: 0,
        headNodX: Math.sin(cycle * 0.5) * 0.05,
      };
    }
    case "idle":
    default: {
      const cycle = t * Math.PI * 1.2;
      return {
        bodyYOffset: Math.sin(cycle) * 0.02,
        bodyTiltX: 0,
        leftArmX: Math.sin(cycle) * 0.03,
        rightArmX: -Math.sin(cycle) * 0.03,
        leftLegX: 0,
        rightLegX: 0,
        headNodX: Math.sin(cycle * 0.7) * 0.02,
      };
    }
  }
}
