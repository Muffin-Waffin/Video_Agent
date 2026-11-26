import * as THREE from "three";

export type Kit = Record<string, THREE.Object3D>;
export const KENNEY_ASSETS: string[] = [];

export function buildWorld(
  root: THREE.Group,
  _kit: Kit
): { update?: (f: number) => void } | void {
  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(200, 200),
    new THREE.MeshStandardMaterial({ color: "#7aa86a", roughness: 0.9 })
  );
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  root.add(ground);
}
