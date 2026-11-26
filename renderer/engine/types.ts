export type Vec3 = [number, number, number];

export type BackgroundPreset = "day" | "sunset" | "night" | "overcast" | "studio";
export type TerrainPreset = "grass" | "sand" | "stone" | "snow" | "none";
export type WaterStyle = "calm" | "rippling" | "river";
export type CharacterAnimation = "idle" | "walk" | "run" | "interact" | "talk" | "wave";
export type CharacterVariant = "default_human" | "casual" | "formal" | "worker" | "explorer";
export type ParticleKind = "smoke" | "fire" | "explosion" | "glow" | "sparkle" | "rain";
export type TransitionKind = "cut" | "fade" | "wipe_left" | "wipe_right" | "zoom_in";

export interface AssetManifestEntry {
  asset_id: string;
  name: string;
  category: "environment" | "living_objects" | "non_living_objects" | "extras";
  asset_type: "3d_model" | "2d_image" | "2d_graphic" | "procedural" | "vfx";
  file_path: string;
  reusable: boolean;
  metadata?: Record<string, unknown>;
}

export interface AssetManifest {
  story_id: string;
  assets: Record<string, AssetManifestEntry>;
}

export interface ShotConfig {
  shot_id: string;
  start_frame: number;
  duration_frames: number;
  narration?: string;
  transition?: TransitionKind;
}
