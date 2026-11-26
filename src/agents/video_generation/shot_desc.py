from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END, START
from dotenv import load_dotenv
from agents.models import (EntityModel,StoryScriptModel,AssetDescBatch,ShotBatch,AssetDesc)
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

    # total_duration = sum(
    #     shot.duration for shot in res.shots
    # )

    print(f"[bold green]Shot generation completed![/bold green] ")
    print(f"Expected audio duration: {audio_duration}")
    # print(f"Generated shot duration: {total_duration:.2f}s")
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
