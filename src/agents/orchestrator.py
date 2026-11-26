"""
    video idea -> video idea validation -> video_highlight.content -> validation -> script genertaion -> audio generation -> shot description ->  video generation -> changes and revision -> video rating, captioning, tags -> validation -> video-posting


    ~ HITL 

    idea validation -> if agent rates the idea above 8 then HITL activates
    video generation -> when agent completes the video and gives the output and user gives the revised changes
    packaging and posting aprroval 
"""
CONFIG = {
    "configurable": {
        "thread_id": "testtt"
    }
} 

from langgraph.graph import StateGraph, END , START
from typing import TypedDict , Annotated , Literal , NotRequired 
from rich import print
from agents.video_generation.asset import get_asset
from agents.ideation.idea import idea_generation_agent
from agents.script_generation.script_agent import script_agent
from agents.models import VideoIdea , HighlightOutput,Highlight , StoryScriptModel, EntityModel, AssetDescBatch
from langgraph.types import interrupt , Command
from langgraph.checkpoint.memory import MemorySaver
from agents.audio_generation.audio import audio_agent
from langgraph.checkpoint.sqlite import SqliteSaver
from agents.video_generation.shot_desc import get_shot
from agents.video_generation.video_generator import render_and_mux_video, video_generation_node
import sqlite3 
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

class StatusState(TypedDict):
    topic : str
    approved_idea_id: NotRequired[int]
    approved_idea: NotRequired[VideoIdea]
    highlights : NotRequired[HighlightOutput]
    approved_highlight_id : NotRequired[int]
    approved_highlight : NotRequired[Highlight]
    script : NotRequired[StoryScriptModel]
    approved_script : NotRequired[bool] = False
    generated_audio_name : NotRequired[str]
    audio_path : NotRequired[str]
    audio_duration : NotRequired[str]
    words_json_path : NotRequired[str]
    entity : NotRequired[EntityModel]
    assets : NotRequired[AssetDescBatch]
    story_id : NotRequired[str]
    final_video_path : NotRequired[str]


from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

serde = JsonPlusSerializer(
    allowed_msgpack_modules=[
        ("agents.models", "VideoIdea"),
        ("agents.models", "HighlightOutput"),
        ("agents.models", "Highlight"),
        ("agents.models", "StoryScriptModel"),
        ("agents.models", "EntityModel"),
        ("agents.models", "IdeaModel"),
        ("agents.models", "IdeaEvaluationBatch"),
        ("agents.models", "AssetDescBatch"),
        ("agents.models", "ShotBatch"),
    ]
)
conn  = sqlite3.connect(
    "video_pipeline.db",
    check_same_thread=False
)

checkpointer = SqliteSaver(conn, serde=serde)

def run_script_agent(state : StatusState):
    return script_agent.invoke({
        "idea": state["approved_idea"]
    })

def run_render_video(state: StatusState):
    story_id = state.get("story_id", "BridgeShort")
    final_path = render_and_mux_video(story_id=story_id, audio_path=state.get("audio_path"))
    return {"final_video_path": final_path}


graph = StateGraph(StatusState)

graph.add_node("idea_generation" , idea_generation_agent)
graph.add_node("script_generation", run_script_agent)
graph.add_node("audio_generation", audio_agent)
graph.add_node("get_asset_requirement" , get_asset)
graph.add_node("get_shot" , get_shot)
graph.add_node("video_generation", video_generation_node)
graph.add_node("render_video", run_render_video)

graph.add_edge(START , "idea_generation")
graph.add_edge("idea_generation" , "script_generation")
graph.add_edge("script_generation" , "audio_generation")
graph.add_edge("audio_generation" , "get_asset_requirement" )
graph.add_edge("get_asset_requirement" , "get_shot" )
graph.add_edge("get_shot" , "video_generation")
graph.add_edge("video_generation" , "render_video")
graph.add_edge("render_video" , END)

workflow = graph.compile(checkpointer=checkpointer)

saved_state = workflow.get_state(CONFIG)
if saved_state and saved_state.next:
    print(f"[bold yellow]Resuming thread '{CONFIG['configurable']['thread_id']}' from {saved_state.next}...[/bold yellow]")
    result = workflow.invoke(None, config=CONFIG)
else:
    topic = input("Enter the topic you want to create video about :")
    result = workflow.invoke({"topic": topic}, config=CONFIG)


while "__interrupt__" in result:
    interrupt_data = result["__interrupt__"][0].value

    print("\n[bold cyan]Human Feedback Needed![/bold cyan]")
    if "ideas" in interrupt_data:
        for idea in interrupt_data["ideas"]:
            print(f"\n{idea['idea']}. {idea['title']}")
            print(idea["concept"])
            print(f"Hook: {idea['hook']}")

        approved_id = int(input("\nEnter the idea ID you approve: "))

        # Resume the PARENT workflow
        result = workflow.invoke(
            Command(
                resume={
                    "approved_idea_id": approved_id
                }
            ),
            config=CONFIG
        )

    elif "highlights" in interrupt_data:
    
            for highlight in interrupt_data['highlights']:
                print(f"Id : {highlight["id"]}.")
                print(f"title : {highlight["title"]}.")
                print(f"description : {highlight["description"]}.")
                print(f"narrative_purpose : {highlight["narrative_purpose"]}.")
                print(f"visual_description : {highlight["visual_description"]}.")
                print(f"overall_score : {highlight["overall_score"]}.")
    
            approved_id = int(input("\nEnter the highlight ID you approve: "))
    
            result = workflow.invoke(
                    Command(
                        resume={
                            "approved_highlight_id": approved_id
                        }
                    ),
                    config=CONFIG
                )
    
            print(result)

    elif "script" in interrupt_data: 
            print(f"Script : {interrupt_data["script"]['script']}")
    
            approved_script = input("\n Would you approve this script (y/n):")
    
            result = workflow.invoke(
                Command(
                    resume = {
                        "approved_script" : approved_script
                    }
                ), 
                    config = CONFIG
            )
    else : 
        raise({
            ValueError:"No Known interrupt available"
        })
    
    print(result)

print(StatusState)