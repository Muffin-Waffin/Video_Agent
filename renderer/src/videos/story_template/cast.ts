import * as THREE from "three";
import { NOINK } from "./ink";

export function buildCast(
  root: THREE.Group
): { update?: (f: number, cam: THREE.PerspectiveCamera) => void } | void {
  const group = new THREE.Group();
  group.layers.set(NOINK);
  root.add(group);
  return {
    update: (_f, cam) => {
      group.quaternion.copy(cam.quaternion);
    },
  };
}
