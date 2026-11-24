from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END , START
from dotenv import load_dotenv
from agents.models import EntityModel , StoryScriptModel, AssetDescBatch , ShotBatch, ShotModel
from typing import TypedDict, NotRequired
from agents.video_generation.prompt import shot_prompt
from video_stuff.guideline_loader import load_visual_guidelines
from rich import print
load_dotenv()

class ShotState(TypedDict):
    assets : AssetDescBatch
    script : StoryScriptModel
    models : EntityModel
    shot_direction : NotRequired[ShotBatch]

llm = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite', temperature = 0.8)

structured_llm = llm.with_structured_output(ShotModel)

def generate_shot_description(state : ShotState):

    shot_direction_list = []

    return{
        "shot_direction" : shot_direction_list
    }