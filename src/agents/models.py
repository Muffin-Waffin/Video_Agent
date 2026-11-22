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

    strengths: list[str]
    weaknesses: list[str]
    suggestions: list[str]

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
    central_question: str
    central_reveal: str

    highlights: list[Highlight] = Field(
        min_length=3,
        max_length=7
    )

    narrative_arc: str
    suggested_ending: str
    