from pydantic import BaseModel , Field
from typing import Optional , Literal

class VideoIdea(BaseModel):
    id: int
    title: str
    category: str
    concept: str
    hook: str
    visual_premise: str
    story_direction: str
    reference_inspiration: Optional[str] = None
    originality_note : str 
    research_required : bool

class IdeaModel(BaseModel):
    ideas: list[VideoIdea] = Field(min_length=5)


class IdeaEvaluation(BaseModel):
    idea_id: int

    hook_strength: float = Field(ge=0, le=10)
    curiosity: float = Field(ge=0, le=10)
    visual_potential: float = Field(ge=0, le=10)
    storytelling: float = Field(ge=0, le=10)
    originality: float = Field(ge=0, le=10)
    feasibility: float = Field(ge=0, le=10)

    overall_score: float = Field(ge=0, le=10)

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    decision: Literal["accept", "revise", "reject"]

class IdeaEvaluationBatch(BaseModel):
    evaluated_ideas : list[IdeaEvaluation]


class Highlight(BaseModel):
    id: int
    title: str
    description: str

    narrative_purpose: Literal[
        "hook",
        "setup",
        "development",
        "twist",
        "climax",
        "payoff"
    ]

    importance: Literal["high", "medium", "low"]

    visual_description: str

    factual_claims: list[str] = Field(
        default_factory=list
    )

    research_status: Literal[
        "verified",
        "unverified",
        "needs_research"
    ]


class HighlightOutput(BaseModel):
    original_topic: str
    central_question: str
    central_reveal: str

    highlights: list[Highlight] = Field(
        min_length=3,
        max_length=7
    )

    narrative_arc: str
    suggested_ending: str

class HighlightEvaluationModel(BaseModel):
    id : int 
    title : str
    concept : str 

    narrative_angle : float = Field(ge=0 , le= 10)
    hook : float = Field(ge=0 , le= 10)
    visual_potential : float = Field(ge=0 , le= 10)
    curiosity_score : float = Field(ge=0 , le= 10)
    storytelling_potential : float = Field(ge=0 , le= 10)
    production_feasibility : float = Field(ge=0 , le= 10)

    overall_score: float = Field(ge=0, le=10)

    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]

    decision: Literal["accept","reject"]

class HighlightEvaluationModelBatch(BaseModel):
    evaluated_highlights : list[HighlightEvaluationModel]


class NarrationBeat(BaseModel):
    beat_type: str = Field(description="Hook, setting, escalation, breaking point, consequence, explanation, or payoff.")
    narration: str = Field(description="The exact narration belonging to this beat.")
    purpose: str = Field(description="What this beat contributes to the story.")


class StoryScriptModel(BaseModel):
    title: str = Field(min_length=4,max_length=80)
    premise: str = Field(description="A concise, one-sentence summary of the story.")
    script: str = Field(description="Complete narration script, ready for voice generation.")
    narration_beats: list[NarrationBeat]
    word_count: int = Field(ge=1,description="Number of spoken words in the narration.")
    claims: list[str] = Field(description="Factual claims that should be verified before publishing.")
    ending_explanation: str = Field(description="Why the ending creates a satisfying payoff or callback.")

class EntityModel(BaseModel):
    environment : list[str] = Field(description="this contains the list of enviornmental objects that are required \n Example: sun, grass, moon , sky, etc")
    living_objects : list[str] = Field(description="this contains the list of living objects. \n example : dogs, cats , main character , living characters , npcs , etc")
    non_living_objects : list[str] = Field(description="this contains the list of all the non living objects in use of the video. Example : bridge, water bottle, phone , glasses , etc")
    extras : list[str] = Field(description="this contains the list of obejcts which you thing are not fitting in he other categories but it is needed in the video")

class AssetDesc(BaseModel):
    asset_id : str = Field(description="this will contain the id the asset is going to have.")
    name : str = Field(description="this will contain the name of the asset we are going to have. Exapmle : Steel Lever")
    category : Literal['environment','living_objects','non_living_objects','extras'] = Field(description="this will contain the category of the asset we are going to have. Exapmle : non_living_objects")
    asset_type :Literal["3d_model","2d_image","2d_graphic","procedural","vfx"] = Field(description="this will contain the type of the assest we are going to have. example : 3d_model")
    visual_description :str = Field(description="this willl have the desciption of the assest we are making. Example : Industrial steel control lever...")
    reusable : bool

class AssetDescBatch(BaseModel):
    assets : list[AssetDesc]

class ShotModel(BaseModel):
    shot_id: str
    narration: str
    duration: float

    visual_description: str

    assets_required: list[str]

    camera: str
    animation: str

    transition: str


class ShotModel(BaseModel):
    shot_id: str = Field(description="A unique identifier for the shot. Example: SHOT_001.")
    narration: str = Field(description="The exact portion of the video narration associated with this shot. It should correspond to the relevant part of the original script.")
    duration: float = Field(description="The estimated duration of this shot in seconds. It should be appropriate for the narration and visual action.")
    visual_description: str = Field(description="A detailed description of everything the viewer should see in this shot, including the environment, characters, objects, their positions, composition, and atmosphere.")
    assets_required: list[str] = Field(description="A list of asset IDs required for this shot. Only reference existing asset IDs from the provided AssetDescBatch. Do not invent new assets.")
    camera: str = Field(description="Describe the camera framing, angle, perspective, and movement. Examples: wide shot, close-up, low angle, dolly in, tracking shot.")
    animation: str = Field(description="Describe the visual actions and movements occurring during this shot, including character movements, object interactions, environmental changes, and visual effects.")
    transition: str = Field(description="Describe how this shot transitions into the next shot. Examples: cut, fade, dissolve, whip pan. Use a suitable transition based on the narrative.")

class ShotBatch(BaseModel):
    shots: list[ShotModel] = Field(description="An ordered list of shots that collectively represent the complete video. Each shot should cover a specific portion of the narration, and together the shots should cover the entire script without unnecessary repetition or missing sections.")

