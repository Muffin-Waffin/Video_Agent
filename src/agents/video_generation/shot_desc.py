from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv
from agents.models import (EntityModel,StoryScriptModel,AssetDescBatch,ShotBatch)
from typing import TypedDict, NotRequired
from agents.video_generation.prompt import shot_prompt
from agents.video_generation.video_stuff.guideline_loader import retrieve_visual_guidelines
from rich import print
import json
from langchain_groq import ChatGroq
load_dotenv()

class ShotState(TypedDict):
    assets: AssetDescBatch
    script: StoryScriptModel
    entity: EntityModel
    audio_duration: str
    shot_direction: NotRequired[ShotBatch]

primary_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite",temperature=0.8 , max_retries= 5)
fallback_llm = ChatGroq(model="openai/gpt-oss-120b" , temperature=0.8 , max_tokens=15000)

llm = primary_llm.with_fallbacks([fallback_llm])

structured_llm = llm.with_structured_output(ShotBatch)

shot_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        shot_prompt
    ),
    (
        "human",
        """
You are receiving the complete video script, available assets,
entity information, audio duration, and visual production guidelines.
Your task is to divide the complete narration into a sequence
of cinematic animation shots.

SCRIPT: {script}
AVAILABLE ASSETS: {assets}
AVAILABLE MODELS: {models}
AUDIO DURATION: {audio_duration}
VISUAL GUIDELINES:{guideline}

INSTRUCTIONS:
1. Generate an ordered sequence of shots covering the entire narration.
2. Every shot must contain the exact portion of narration
   associated with that visual.
3. The combined shot durations should approximately match
   the total audio duration.
4. Only reference asset IDs provided in the available assets.
   Do not invent new asset IDs.
5. Maintain visual and narrative continuity between shots.
6. Use appropriate camera framing, angles, and movements.
7. Describe character actions, object interactions,
   environmental changes, and animation clearly.
8. Use transitions that make sense between consecutive shots.
9. Avoid unnecessary repetition of visuals.
10. Make each shot visually engaging and suitable for
    short-form animated video production.
Return the result using the supplied structured schema.
"""
    )
])
shot_chain = shot_prompt | structured_llm

def generate_shot_description(state: ShotState):
    script = state["script"]
    assets = state["assets"]
    models = state["entity"]
    audio_duration = state["audio_duration"]

    guideline = retrieve_visual_guidelines(
        query=f"""
        Find visual production guidelines relevant to generating
        cinematic animation shots for the following story:

        Story:
        {script}

        Focus on:
        - Shot composition and framing
        - Camera angles and perspectives
        - Camera movements
        - Visual storytelling and scene continuity
        - Character positioning and screen direction
        - Lighting, atmosphere, and depth
        - Animation principles and movement
        - Shot duration and visual pacing
        - Scene transitions and continuity
        - Matching visuals with narration
        - Maintaining a consistent visual style

        Retrieve practical guidelines for creating visually
        engaging and coherent animated shots.
        """,
        k=7
    )

    res = shot_chain.invoke({
        "script": script,
        "assets": assets,
        "models": models,
        "audio_duration": audio_duration,
        "guideline": guideline
    })

    total_duration = sum(
        shot.duration for shot in res.shots
    )

    print(f"[bold green]Shot generation completed![/bold green] ")
    print(f"Expected audio duration: {audio_duration}")
    print(f"Generated shot duration: {total_duration:.2f}s")
    print(f"Number of shots: {len(res.shots)}")
    # if abs(total_duration - audio_duration) > 1.0:
    #     print(
    #         "[yellow]Warning: Shot duration differs "
    #         "from audio duration by more than 1 second.[/yellow]"
    #     )

    with open("shot_direction.json", "w", encoding="utf-8") as file:
        json.dump(
            res.model_dump(mode="json"),
            file,
            indent=4,
            ensure_ascii=False
        )
    return {
        "shot_direction": res
    }


graph = StateGraph(ShotState)
graph.add_node("generate_shots",generate_shot_description)
graph.add_edge(START,"generate_shots")
graph.add_edge("generate_shots",END)
get_shot = graph.compile()


test = {
  "assets": [
    {
      "asset_id": "ENV_RETRO_VIRTUAL_WORLD_TERRAIN",
      "name": "Retro Virtual World Terrain",
      "category": "environment",
      "asset_type": "3d_model",
      "visual_description": "Stylized retro virtual world terrain featuring a modular architectural layout with neutral lighter stone block courses and cobble sett arrangements. Incorporates two-tone shaded materials utilizing albedo mixed with specific lit and shade color pairs. Features detailed timber beams with visible grain strokes, iron components in muted steel tones, and water texture integration with crests, troughs, and glints.",
      "reusable": True
    },
    {
      "asset_id": "ENV_digital_grid_background",
      "name": "digital grid background",
      "category": "environment",
      "asset_type": "procedural",
      "visual_description": "A precise digital grid environment background featuring anti-aliased geometry lines with a neutral near-black base colour of #0b0a0c. The lines maintain a nearly constant screen width between 2.15 px and 3.36 px, showing crisp vector-like sharpness with a rise of 1.45 px at 720 resolution. Cores exhibit luma values from 7 to 50, with subtle bleeding caused by chroma subsampling and atmospheric depth, creating a clean, high-tech receding perspective without excessive blur.",
      "reusable": True
    },
    {
      "asset_id": "ENV_computer_terminal_interior",
      "name": "Computer Terminal Interior",
      "category": "environment",
      "asset_type": "3d_model",
      "visual_description": "A stylised 3D toon-shaded computer terminal interior environment rendered with hand-painted textures and a saturated color palette. The geometry features distinct thin black ink outlines in #241726 on all edges and creases. Walls and surfaces are styled with muted pastel and deep contrasting tones (cream #f3e6d2, aqua #a3cdc7, and deep near-black shadow areas). The lighting utilizes warm key highlights paired with rich blue and purple shadows, producing soft depth of field and distinct light pools that tint internal props. All materials adhere to a two-tone toon lighting model with strong stylistic line work.",
      "reusable": True
    },
    {
      "asset_id": "ENV_001",
      "name": "Gaming Room Late Twentieth Century",
      "category": "environment",
      "asset_type": "3d_model",
      "visual_description": "A late 20th-century gaming room environment rendered in a stylized 3D toon art style. The scene features chunky CRT monitors displaying glowing pixelated interfaces, a bulky beige computer tower with visible floppy drives and ventilation slits, a cluttered wooden desk with a boxed keyboard and ball mouse, and wood-paneled walls decorated with vintage gaming posters. The 3D geometry is outlined with thick-thin ink lines (#241726) along all edges and creases. Hand-painted textures utilize saturated colors with warm key lighting and blue-purple soft shadows. Cluttered props characteristic of the era, such as tangled cables, plastic cassette cases, and soda cans, are scattered across the surfaces to tell a visual story.",
      "reusable": True
    },
    {
      "asset_id": "CHR_001",
      "name": "retro game player avatar",
      "category": "living_objects",
      "asset_type": "3d_model",
      "visual_description": "A stylized 3D avatar designed for a retro game player character, featuring clean proportions and distinct retro-inspired uniform elements. The character has a bright skin fill (#ffe2c2, #f5c9a0) with soft crescent skin shading in warmer tones, lidded deadpan eyes spaced 0.26 W apart on the centre line, thicker tapered brows, and a small mouth. The avatar wears a rifle-green coatee jacket (#357650) with white cross belts (#f1efe6), pewter buttons (#d9dde0), dark trousers (#3d4440), and a shako hat with a grey body (#3a3d47), black peak (#16171b), silver badge (#c9ccd2), and green tuft (#2b7a4b). Outlines use a thick-thin plum ink stroke (#241726) measuring approximately 5% width with dynamic variation. The asset strictly avoids cheek blush and visible surface grain, maintaining bright, readable lighting values.",
      "reusable": True
    },
    {
      "asset_id": "CHR_001",
      "name": "Ordinary Character",
      "category": "living_objects",
      "asset_type": "3d_model",
      "visual_description": "An ordinary character featuring a stylized aesthetic with a thick-thin plum outline using INK color #241726, variable thickness, and a lifted on-screen ink shade from #0a0014 to #2a1b28. The face has lidded deadpan eyes spaced 0.26 W apart on the centre line, thicker tapered brows at -0.20 W, and a small mouth at +0.20 W with no blush or catchlights. Skin fill uses brighter tones such as #ffe2c2, #f5c9a0, #ecd0b6, or #c99067, rendering with a high luma value >=0.85 and a soft lavender-tinted crescent shadow on the side away from the light. Clothing follows a clean palette with no surface grain, featuring a broad gradient on the torso and a consistent, clear silhouette suitable for animated video production.",
      "reusable": True
    },
    {
      "asset_id": "CHR_001",
      "name": "Game Designers",
      "category": "living_objects",
      "asset_type": "3d_model",
      "visual_description": "Stylized 3D character representing a game designer, adhering strictly to the production visual guidelines. Proportions feature a slightly stylized large head with a high face luma exceeding 0.85, skin fill of bright tones like #ffe2c2, and a distinct thick-thin plum ink outline using color #241726 with the thicker side oriented away from the light. Facial features include 0.26 W spaced lidded deadpan eyes with no catchlights, thicker tapered brows, and a small mouth shifted slightly toward the facing side. The character wears creative professional attire rendered in flat colors with soft crescent head shading and broad torso gradients, avoiding complex grain or excessive textures. Includes a soft ground blob shadow and clean, readable silhouette matching the required stylized animation aesthetic.",
      "reusable": True
    },
    {
      "asset_id": "CHR_crowd_of_players",
      "name": "crowd of players",
      "category": "living_objects",
      "asset_type": "3d_model",
      "visual_description": "A stylized crowd of 2D flat cartoon characters functioning as players in a 3D toon environment. Each character features a thick-thin plum outline using INK color #241726, bright clean skin fills (#ffe2c2, #f5c9a0, #ecd0b6, #c99067) with luma >=0.85, soft crescent skin shadows, and a deadpan facial expression with lidded eyes, no blush, and tapered brows. They wear rifle-green coatees (#357650) with white cross belts (#f1efe6), pewter or brass buttons, dark grey trousers (#3d4440), and shako hats with body #3a3d47 and green tufts. The group exhibits distinct proportions with a consistent cel-shaded look matching the hand-painted 3D environment.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_INFINITE_DAMAGE_CANNON",
      "name": "infinite damage cannon",
      "category": "non_living_objects",
      "asset_type": "3d_model",
      "visual_description": "A heavy, stylized artillery piece crafted with weathered oak timber plates in warm brown tones (#a8743f, #9e6b39, #b07a44) featuring dark seams, grain strokes, and bolted iron joints in #2f2a2a. The carriage and reinforcement plates integrate stone-textured blocks (#ddd0bf, #d3c5b3, #e5d9c9) with mortar lines in #a39584. Outlined entirely with a thick-thin plum ink stroke (#241726) following a cel-shaded visual style. Metal elements feature rifle-green #357650 accents, pewter buttons (#d9dde0), and a massive stylized barrel designed to deliver exaggerated, comical amounts of infinite damage within a hand-painted 3D toon environment.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_corrupted_weapon_payload",
      "name": "Corrupted Weapon Payload",
      "category": "non_living_objects",
      "asset_type": "3d_model",
      "visual_description": "A stylized military payload object shaped like a vertical capsule or bean, featuring a distinct thick-thin plum outline using INK color #241726 with the thick side oriented away from the light and toward the ground. The surface is colored in dark aubergine and plum tones (L* 16-22) rather than pure black, avoiding boxy corners in favor of fully rounded organic proportions. The object incorporates corrupted elements showing a mix of military green (#357650) and oxidized yellow-green or rusty orange metallic plating (#e3b684), with smooth gradients shifting across the torso and an optional soft rim light on the shadow edge. Inner details and structural paneling sit neatly within the 0.4-0.9 scale range with zero to minimal surface grain.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_retro_computer_monitor",
      "name": "Retro Computer Monitor",
      "category": "non_living_objects",
      "asset_type": "3d_model",
      "visual_description": "A chunky, 1980s-style CRT computer monitor with an off-white and cream molded plastic housing colored in #fef9f6 and #ffe0b4. The form is blocky with gently rounded corners and slight yellowing aging on the underside. The screen is inset, displaying a muted dark tone (#af9886) with a subtle emissive glow. Outlined with a thick-thin plum ink stroke (#241726) following dynamic width variations. The surface features clean flat shading with no visible texture grain, adhering to a bright aesthetic with high luma values.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_mechanical_odometer",
      "name": "Mechanical Odometer",
      "category": "non_living_objects",
      "asset_type": "3d_model",
      "visual_description": "A vintage mechanical odometer featuring a metallic casing rendered in dark iron #4b5468 with painted highlight bands. The unit is framed by a thick-thin plum outline using INK #241726 with dynamic line thickness. The analog number drums display crisp typography against a light cream and white fill (#fef9f6 / #e7edf5) with a median luma of 0.93. The surface exhibits no visible film grain or procedural noise, maintaining a clean, high-contrast industrial aesthetic with soft crescent shading and subtle lavender tinting on shadowed edges.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_health_bar_ui",
      "name": "Health Bar UI",
      "category": "non_living_objects",
      "asset_type": "2d_graphic",
      "visual_description": "A clean, high-resolution health bar user interface element featuring a crisp thick-thin plum outline using ink color #241726 with width variation. The interior fill consists of a creamy, bright surface with tones #fef9f6 and #e7edf5, framed with anti-aliased lines maintaining a near-constant screen width. The graphic incorporates neutral near-black elements (#0b0a0c), flat untextured shading with no visible grain, and precise geometric proportions designed to remain sharp and readable at standard resolutions without relying on artificial blurring.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_damage_counter_ui",
      "name": "Damage Counter UI",
      "category": "non_living_objects",
      "asset_type": "2d_graphic",
      "visual_description": "A flat 2D graphic user interface element serving as a damage counter, rendered in a distinct illustrated style. It features a clean, high-luma face fill with a high-key skin tone of #f7d6b6, bounded by a thick-thin plum outline using ink color #241726. The ink outline has a varying thickness with the thick side oriented away from the light source and toward the bottom. Inner details are scaled between 0.4 and 0.9x with lifted on-screen ink ranging from #0a0014 to #2a1b28. The face includes deadpan lidded eyes positioned 0.26 W apart on the center line, thicker tapered brows at -0.20 W, and a small mouth at +0.20 W with no blush or catchlights. The entire element is clean with zero measurable grain and sharp anti-aliased lines maintaining consistent pixel width.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_MEMORY_REGISTER_BOX",
      "name": "Memory Register Box",
      "category": "non_living_objects",
      "asset_type": "3d_model",
      "visual_description": "A rectangular metallic data storage and memory register housing, designed with precise industrial proportions. The main body features a dark iron-grey finish colored in M.iron #4b5468, avoiding pure black to maintain visible surface detail and highlights. The top and bottom lips feature distinct lit and shaded bevels rendered with subtle lighting gradients, with an integrated surface grain texture that remains seamless and never reads as physical gaps. Detailed with fine dark seams #4a2510, integrated metal bolts #2f2a2a, and structural reinforcement plates matching the iron-and-timber stylistic guidelines. The overall surface resolution accommodates a high-density 1024 texels/m ratio, ensuring crisp edges, controlled luma values never falling below L* 19, and a thick-thin plum ink outline style (#241726) framing its silhouette.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_game_cartridge",
      "name": "Game Cartridge",
      "category": "non_living_objects",
      "asset_type": "3d_model",
      "visual_description": "A rectangular retro-style game cartridge with clean, flat surfaces and rounded top corners. The main casing is molded from durable matte plastic colored in a soft cream off-white #fef9f6, featuring subtle beveled edges and a recessed label area on the front face. The label surface utilizes a light grey-blue #e7edf5 background with minimal printed graphic accents in dark ink #241726. The bottom edge has a standard exposed multi-pin connector slot made of brass-toned metallic contacts. The entire object is outlined with a thick-thin stylized ink stroke #241726 following the established visual guideline, featuring flat shading with no visible surface grain or texture.",
      "reusable": True
    },
    {
      "asset_id": "VFX_glitch_code_streams",
      "name": "Glitch Code Text Streams",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "Dynamic vertical data streams consisting of corrupted digital text and binary characters falling in cascading patterns. The lines feature a neutral near-black ink color #0b0a0c with chromatic aberration smear of 2 to 3 pixels wide showing faint chroma subsampling hues. Line widths remain nearly constant on screen at approximately 3.09 pixels with sharp, anti-aliased edges and occasional digital distortion flicker. Integrates subtle DOF blurring for background streams and glowing glitch artifacts.",
      "reusable": True
    },
    {
      "asset_id": "VFX_overflowing_numerical_values",
      "name": "Overflowing Numerical Values",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "A cascade of cascading 2D flat cartoon numbers and mathematical digits overflowing in a chaotic stream. Styled with a thick-thin plum outline using INK #241726, featuring a variable line thickness where the thick side is oriented away from the light and toward the ground. The inner fill uses clean white and cream tones ranging from #fef9f6 to #e7edf5 with zero grain, rendered with high luma values around 0.85 to 0.93. The numbers tumble and spill dynamically with soft lavender shadow tints, maintaining a consistent 2D hand-drawn toon aesthetic while interacting with the 3D scene lighting.",
      "reusable": True
    },
    {
      "asset_id": "VFX_001",
      "name": "Screen-Clearing Energy Blast",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "A high-intensity, screen-clearing energy blast visual effect featuring a wide horizontal wave of glowing plasma. The core emits a high dynamic range emissive glow with HDR color coordinates (8, 6, 3) for intense sparking and bolt snaps, fading smoothly into a broader luminance-controlled aura. Utilizes precise bloom settings with a luminance threshold of 1.0, intensity of 0.5, and radius of 0.6 to ensure crisp white centers without blooming out entirely. Framed by a thick-thin plum ink outline (#241726) with variable stroke weight depending on proximity to the primary light source. The particle system combines flat 2D cartoon sprites, light shafts, and dynamic sparks composited directly into the 3D scene, maintaining clean lines, zero procedural grain, and an anime-styled aesthetic.",
      "reusable": True
    },
    {
      "asset_id": "OBJ_system_crash_warning_prompt",
      "name": "System Crash Warning Prompt",
      "category": "non_living_objects",
      "asset_type": "2d_graphic",
      "visual_description": "A 2D graphic warning prompt rendered in a stylized flat cartoon aesthetic with a thick-thin plum outline using INK #241726. The interior fill features an off-screen elevated luma value around #af9886 with a median luma of 0.62. The prompt displays a minimalist deadpan expression featuring lidded deadpan eyes spaced 0.26 W apart on the center line, thicker tapered brows at -0.20 W, and a small mouth at +0.20 W with no blush or catchlights. The overall structure maintains clean, anti-aliased geometry lines without grain, fitting seamlessly into 3D toon environments with a crisp, stylized presentation.",
      "reusable": True
    },
    {
      "asset_id": "VFX_garbage_data_stream_particles",
      "name": "Garbage Data Stream Particles",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "A stylized visual effect representing a stream of corrupted digital garbage data. Composed of floating, anti-aliased pixel fragments and abstract glyphs flowing in a directional current. Outlined with thick-thin plum ink strokes using color #241726. The inner core uses neutral near-black #0b0a0c with chromatic smearing and subtle chroma subsampling edges. Features high-luminance values (luma >=0.85) to stand out against dark backgrounds, maintaining a crisp vector-like sharpness with 1.45 px rise and minimal grain.",
      "reusable": True
    },
    {
      "asset_id": "VFX_SPARKLES_IMPACT_01",
      "name": "Sparkles on Impact",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "Dynamic impact spark particle effect featuring high-intensity HDR emissive colour values of (8, 6, 3) designed for bloom integration with luminance threshold 1.0. Individual spark debris pieces exhibit crisp white heads transitioning into glowing golden-orange trails. Shaped as sharp, high-velocity geometric streaks radiating outward from the collision point, adhering to stylized thick-thin plum outlines (#241726) with zero surface grain and intense self-illumination matching high bloom intensity parameters.",
      "reusable": True
    },
    {
      "asset_id": "VFX_speed_lines",
      "name": "Speed Lines",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "Flat 2D cartoon sprite speed lines for motion emphasis. Consists of near-black anti-aliased lines using neutral near-black hex color #0b0a0c, maintaining a sharp rise of 1.45 px at 720p resolution without blur. The line width stays nearly constant on screen across near, mid, and far distances, measuring approximately 3.09 to 2.82 px, with subtle chroma smear and atmosphere lightening on distant elements.",
      "reusable": True
    },
    {
      "asset_id": "VFX_01",
      "name": "Light Rays",
      "category": "extras",
      "asset_type": "vfx",
      "visual_description": "Volumetric golden sun light rays with atmospheric bloom and haze. Features a radiant glow spanning approximately 13 to 26 percent of the frame width at the edges. Integrates soft atmospheric scattering with pink, peach, and warm golden illumination, maintaining clean edges without specular highlights on non-metal surfaces.",
      "reusable": True
    }
  ],
  "script": {
    "title": "The Glitch That Built a God-Gun",
    "premise": "A programming oversight intended to crash a retro video game instead bypassed memory limits to create an infinite damage weapon.",
    "script": "This tiny coding mistake was supposed to crash the game, but instead, it created an infinite damage cannon. It is the late twentieth century, and players exploring a retro virtual world stumble into a bizarre computational blind spot. The game engine tries to read a memory register sitting far outside its legal boundaries. Normally, this severe oversight triggers an immediate, hard system crash. But through pure digital coincidence, the missing boundary check allows garbage data to spill directly into the active weapon payload slot. Players quickly realize that firing this corrupted item does not freeze the screen. Instead, it multiplies numerical values endlessly with every single frame. The damage counter overflows, shattering health bars and turning ordinary characters into screen-clearing powerhouses. You see, computers rely on strict numerical limits, much like an odometer that rolls back over to zero after reaching its maximum. When the game forced the overflowed register into the weapon stats, it looped the numbers straight into maximum capacity. The game designers patched the engine years ago, but the legendary weapon remains embedded in digital folklore as the ultimate accidental super weapon.",
    "narration_beats": [
      {
        "beat_type": "Hook",
        "narration": "This tiny coding mistake was supposed to crash the game, but instead, it created an infinite damage cannon.",
        "purpose": "Grab attention immediately with the paradox of a crash turning into a super weapon."
      },
      {
        "beat_type": "Setting",
        "narration": "It is the late twentieth century, and players exploring a retro virtual world stumble into a bizarre computational blind spot.",
        "purpose": "Establish the retro gaming setting and the context of the discovery."
      },
      {
        "beat_type": "Escalation",
        "narration": "The game engine tries to read a memory register sitting far outside its legal boundaries. Normally, this severe oversight triggers an immediate, hard system crash.",
        "purpose": "Explain the technical cause and what was supposed to happen."
      },
      {
        "beat_type": "Breaking Point",
        "narration": "But through pure digital coincidence, the missing boundary check allows garbage data to spill directly into the active weapon payload slot.",
        "purpose": "Show the precise moment the system failure mutates into an exploit."
      },
      {
        "beat_type": "Consequence",
        "narration": "Players quickly realize that firing this corrupted item does not freeze the screen. Instead, it multiplies numerical values endlessly with every single frame. The damage counter overflows, shattering health bars and turning ordinary characters into screen-clearing powerhouses.",
        "purpose": "Show the chaotic and overpowered results of the glitch in action."
      },
      {
        "beat_type": "Explanation",
        "narration": "You see, computers rely on strict numerical limits, much like an odometer that rolls back over to zero after reaching its maximum. When the game forced the overflowed register into the weapon stats, it looped the numbers straight into maximum capacity.",
        "purpose": "Clarify the memory overflow concept using an everyday analogy."
      },
      {
        "beat_type": "Payoff",
        "narration": "The game designers patched the engine years ago, but the legendary weapon remains embedded in digital folklore as the ultimate accidental super weapon.",
        "purpose": "Provide a memorable conclusion looping back to the opening hook."
      }
    ],
    "word_count": 217,
    "claims": [
      "A memory boundary check failed in the retro game engine.",
      "The error code was designed to trigger a crash.",
      "Numerical overflow created massive damage values in retro game programming."
    ],
    "ending_explanation": "The ending creates a satisfying payoff by contrasting the temporary nature of software patches with the permanent legacy of the glitch in gaming culture, bringing the narrative full circle back to the opening hook about the infinite damage cannon."
  },
  "entity": {
    "environment": [
      "retro virtual world terrain",
      "digital grid background",
      "computer terminal interior",
      "gaming room late twentieth century"
    ],
    "living_objects": [
      "retro game player avatar",
      "ordinary character",
      "game designers",
      "crowd of players"
    ],
    "non_living_objects": [
      "infinite damage cannon",
      "corrupted weapon payload",
      "retro computer monitor",
      "mechanical odometer",
      "health bar UI",
      "damage counter UI",
      "memory register box",
      "game cartridge"
    ],
    "extras": [
      "glitch code text streams",
      "overflowing numerical values",
      "screen-clearing energy blast",
      "system crash warning prompt",
      "garbage data stream particles",
      "sparkles on impact",
      "speed lines",
      "light rays"
    ]
  },
  "audio_duration": "77.175"
}

workflow = get_shot.invoke(test)
print(get_shot.get_graph().draw_mermaid())
