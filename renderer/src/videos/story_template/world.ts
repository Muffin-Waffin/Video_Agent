import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { staticFile } from "remotion";
import { LIGHTS } from "./lights";
import { buildWorld, KENNEY_ASSETS, Kit } from "./build";
import { buildCast } from "./cast";
import { Light, SHOTS, camAt } from "./story";

let kitP: Promise<Kit> | null = null;
export const loadKit = (): Promise<Kit> => {
  if (!kitP) {
    const loader = new GLTFLoader();
    kitP = Promise.all(
      KENNEY_ASSETS.map((n) =>
        loader
          .loadAsync(staticFile(`bridge/kenney/${n}.glb`))
          .then((g) => [n, g.scene] as const)
          .catch(() => [n, null] as const)
      )
    ).then(
      (list) => Object.fromEntries(list.filter((e) => e[1]).map(([n, s]) => [n, s!])) as Kit
    );
  }
  return kitP;
};

export class World {
  root = new THREE.Group();
  private skyMat: THREE.ShaderMaterial;
  private dirLight: THREE.DirectionalLight;
  private hemiLight: THREE.HemisphereLight;
  private worldCtrl: { update?: (f: number) => void } | void;
  private castCtrl: { update?: (f: number, cam: THREE.PerspectiveCamera) => void } | void;
  private lastPreset: Light | null = null;

  constructor(kit: Kit) {
    const skyGeo = new THREE.SphereGeometry(600, 24, 16);
    this.skyMat = new THREE.ShaderMaterial({
      side: THREE.BackSide,
      depthWrite: false,
      uniforms: {
        uTop: { value: new THREE.Color("#3e7fd2") },
        uHor: { value: new THREE.Color("#b8d0ec") },
        uSat: { value: 1.08 },
      },
      vertexShader: `varying vec3 vPos; void main(){ vPos = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }`,
      fragmentShader: `
        uniform vec3 uTop; uniform vec3 uHor; uniform float uSat; varying vec3 vPos;
        void main(){
          float h = clamp(normalize(vPos).y * 1.4, 0.0, 1.0);
          vec3 col = mix(uHor, uTop, pow(h, 0.65));
          float l = dot(col, vec3(0.299, 0.587, 0.114));
          col = mix(vec3(l), col, uSat);
          gl_FragColor = vec4(col, 1.0);
        }`,
    });
    this.root.add(new THREE.Mesh(skyGeo, this.skyMat));

    this.dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    this.dirLight.position.set(20, 40, 20);
    this.dirLight.castShadow = true;
    this.root.add(this.dirLight);

    this.hemiLight = new THREE.HemisphereLight(0xb8d0ec, 0x444455, 0.6);
    this.root.add(this.hemiLight);

    this.worldCtrl = buildWorld(this.root, kit);
    this.castCtrl = buildCast(this.root);
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene): THREE.Vector3 {
    const shot = SHOTS[Math.max(0, Math.min(SHOTS.length - 1, id - 1))];
    const preset: Light = shot?.light ?? "day";

    if (this.lastPreset !== preset) {
      this.lastPreset = preset;
      const l = LIGHTS[preset];
      this.skyMat.uniforms.uTop.value.set(l.top);
      this.skyMat.uniforms.uHor.value.set(l.hor);
      this.dirLight.color.setRGB(l.lit[0], l.lit[1], l.lit[2]);
      scene.fog = new THREE.Fog(l.fog, l.fogNear, l.fogFar);
      scene.background = new THREE.Color(l.hor);
    }

    const c = camAt(id, f);
    cam.position.set(...c.pos);
    cam.fov = c.fov;
    cam.updateProjectionMatrix();
    const target = new THREE.Vector3(...c.look);
    cam.lookAt(target);
    if (c.roll) {
      cam.rotateZ((c.roll * Math.PI) / 180);
    }

    this.worldCtrl?.update?.(f);
    this.castCtrl?.update?.(f, cam);
    return target;
  }
}
