export type V3 = [number, number, number];
export type Light = "day" | "golden";
export type ShotDef = { id: number; a: number; b: number; light: Light };
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
export const TOTAL = 1620;
export const FLASH_AT = 775;
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 180, light: 'day' },
  { id: 2, a: 180, b: 360, light: 'golden' },
  { id: 3, a: 360, b: 600, light: 'day' },
  { id: 4, a: 600, b: 840, light: 'day' },
  { id: 5, a: 840, b: 1140, light: 'day' },
  { id: 6, a: 1140, b: 1380, light: 'golden' },
  { id: 7, a: 1380, b: 1620, light: 'day' }
];
export const layersAt = (f: number): { id: number; alpha: number }[] => {
  if (f < 180) return [{ id: 1, alpha: 1 }];
  if (f < 360) return [{ id: 2, alpha: 1 }];
  if (f < 600) return [{ id: 3, alpha: 1 }];
  if (f < 840) return [{ id: 4, alpha: 1 }];
  if (f < 1140) return [{ id: 5, alpha: 1 }];
  if (f < 1380) return [{ id: 6, alpha: 1 }];
  return [{ id: 7, alpha: 1 }];
};
export const camAt = (id: number, f: number): Cam => {
  const p = Math.max(0, Math.min(1, f / 1620));
  switch (id) {
    case 1:
      return { pos: [0, 2, 8 - p * 2], look: [0, 0, 0], fov: 45, roll: 0 };
    case 2:
      return { pos: [-2 + p * 0.5, 3 - p * 0.2, 5 - p * 0.5], look: [0, 1, 0], fov: 50, roll: 0 };
    case 3:
      return { pos: [0, 1.5, 3 - p * 0.5], look: [0, 1, 0], fov: 40, roll: 0 };
    case 4:
      return { pos: [0, 0, 5 - p * 1], look: [0, 0, 0], fov: 55, roll: Math.sin(f * 0.1) * 2 };
    case 5:
      return { pos: [0, 5 + p, 10 - p * 2], look: [0, 2, 0], fov: 60, roll: 0 };
    case 6:
      return { pos: [0, 3 - p * 0.5, 7 - p * 2], look: [0, 1, 0], fov: 50, roll: 0 };
    default:
      return { pos: [0, 2, 4 - p * 0.5], look: [0, 1, 0], fov: 45, roll: 0 };
  }
};
export const dofAt = (f: number): { cInf: number; focus?: (f: number) => V3 } => {
  return { cInf: 10, focus: () => [0, 0, 0] };
};
