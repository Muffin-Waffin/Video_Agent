import * as THREE from 'three';
import { Pen } from './toon';
import { NOINK } from './ink';
export function buildCast(root: THREE.Group):
  | void
  | {
      update?: (f: number, cam: THREE.PerspectiveCamera) => void;
    } {
  const group = new THREE.Group();
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#ffcc00';
    ctx.beginPath();
    ctx.arc(128, 128, 64, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = '#241726';
    ctx.lineWidth = 6;
    ctx.stroke();
  }
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({ map: texture });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(2, 2, 1);
  sprite.position.set(0, 1, 0);
  group.add(sprite);
  root.add(group);
  return {
    update: (f: number, cam: THREE.PerspectiveCamera) => {
      sprite.position.y = 1 + Math.sin(f * 0.1) * 0.1;
    }
  };
}
