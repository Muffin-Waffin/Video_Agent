export type V3 = [number, number, number];
export type Light = "day" | "golden";
export type ShotDef = { id: number; a: number; b: number; light: Light };
export type Cam = { pos: V3; look: V3; fov: number; roll: number };

export const TOTAL = 300;
export const FLASH_AT = -1;
export const SHOTS: ShotDef[] = [{ id: 1, a: 0, b: 300, light: "day" }];

export const layersAt = (f: number): { id: number; alpha: number }[] => {
  const s = SHOTS.find((x) => f >= x.a && f < x.b) ?? SHOTS[SHOTS.length - 1];
  return [{ id: s.id, alpha: 1 }];
};

export const camAt = (_id: number, f: number): Cam => ({
  pos: [0, 3, 10 - f * 0.01],
  look: [0, 1.5, 0],
  fov: 42,
  roll: 0,
});

export const dofAt = (_f: number): { cInf: number; focus?: (f: number) => V3 } => ({
  cInf: 0,
});
