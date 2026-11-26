import * as THREE from 'three';
export type Kit = Record<string, THREE.Object3D>;
export const KENNEY_ASSETS: string[] = [
  'nature_kit_ground_grass',
  'furniture_kit_computerScreen',
  'blank_void_env_01',
  'modern_game_studio_01',
  'game_developers_01',
  'game_designers_001',
  'non_living_objects_mainframe_001',
  'non_living_objects_register_01',
  'non_living_graphics_card_01',
  'non_living_objects_calculator_001',
  'non_living_objects_computer_01',
  'memory_request_surge_01',
  'data_loop_001',
  'coordinate_buffer_01',
  'fracture_effect_01',
  'asset_sun_shaft_01',
  'light_patch_01'
];
export function buildWorld(root: THREE.Group, kit: Kit): { update?: (f: number) => void } | void {
  const group = new THREE.Group();
  if (kit['modern_game_studio_01']) {
    const studio = kit['modern_game_studio_01'].clone();
    studio.position.set(0, 0, 0);
    group.add(studio);
  }
  if (kit['blank_void_env_01']) {
    const voidEnv = kit['blank_void_env_01'].clone();
    voidEnv.position.set(0, -1, 0);
    group.add(voidEnv);
  }
  root.add(group);
  return {
    update: (f: number) => {
      group.rotation.y = f * 0.001;
    }
  };
}
