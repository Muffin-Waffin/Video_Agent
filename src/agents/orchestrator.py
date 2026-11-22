"""
    video idea -> video idea validation -> video_highlight.content -> validation -> video generation -> changes and revision -> video rating, captioning, tags -> validation -> video-posting


    ~ HITL 

    idea validation -> if agent rates the idea above 8 then HITL activates
    video generation -> when agent completes the video and gives the output and user gives the revised changes
    packaging and posting aprroval 
"""

from langgraph.graph import StateGraph, END , START
from typing import TypedDict , Annotated , Literal , NotRequired 
from rich import print
from agents.ideation.idea import idea_generation_agent
from agents.script_generation.script_agent import script_agent
from agents.models import VideoIdea , HighlightOutput
from langgraph.types import interrupt , Command
from langgraph.checkpoint.memory import MemorySaver

class StatusState(TypedDict):
    topic : str
    approved_idea_id: NotRequired[int]
    approved_idea: NotRequired[VideoIdea]
    highlights : NotRequired[HighlightOutput]

def run_script_agent(state : StatusState):
    return script_agent.invoke({
        "idea": state["approved_idea"]
    })

graph = StateGraph(StatusState)

graph.add_node("idea_generation" , idea_generation_agent)
graph.add_node("script_generation", run_script_agent)
graph.add_edge(START , "idea_generation")
graph.add_edge("idea_generation" , "script_generation")
graph.add_edge("script_generation" , END)
checkpointer = MemorySaver()
config = {
    "configurable": {
        "thread_id": "video-001"
    }
} 

workflow = graph.compile(checkpointer=checkpointer)
topic = input("Enter the topic you want to create video about :")

result = workflow.invoke({
    "topic" : topic } , config=config)

if '__interrupt__' in result:
    interrupt_data = result["__interrupt__"][0].value  

    print("\n[bold cyan]Shortlisted Ideas[/bold cyan]")

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
        config=config
    )

print(result)





