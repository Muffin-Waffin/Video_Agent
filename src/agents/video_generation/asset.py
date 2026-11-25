from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END , START
from dotenv import load_dotenv
from agents.models import EntityModel , StoryScriptModel, AssetDesc, AssetDescBatch
from typing import TypedDict, NotRequired
from agents.video_generation.prompt import asset_list_prompt , asset_desc_prompt
from agents.video_generation.video_stuff.guideline_loader import retrieve_visual_guidelines
from rich import print
import json
from langchain_openai import ChatOpenAI
import asyncio
load_dotenv()

# llm = ChatOpenAI(
#     model="local-model",
#     base_url="http://localhost:1235/v1",
#     api_key="lm-studio",
#     temperature=0.8,
# )


class EntityState(TypedDict):
    script : StoryScriptModel
    entity : NotRequired[EntityModel]
    assets : NotRequired[AssetDescBatch]

llm = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite', temperature = 0.8)
prompt = ChatPromptTemplate([
    (
        "system" , asset_list_prompt
    ),
    (
        "human" , """
        you are reciving the StoryScriptModel object which has all the relevent info about the idea 
        your task is to return the required entity you think are going to be needed and generate them
        you will also recevive an guideline paragraph too
        
        Guideline : {guideline}
        StoryScript : {storyscript}
        
        Your task is to identify every visual entity required
        to represent the story through animation.

        Return the entities using the supplied structured schema.

        Do not generate the assets themselves."""
    )
])

asset_prompt = ChatPromptTemplate([
    ("system" , asset_desc_prompt ),(
        "human" , """
        you are receiving the asset_name and a guideline generate the description of the asset.

        Asset : {asset_name}
        Guideline : {guideline}
"""
    )
])

asset_llm = llm.with_structured_output(EntityModel)
entity_chain = prompt | asset_llm 

asset_desc_llm = llm.with_structured_output(AssetDesc)
asset_chain = asset_prompt | asset_desc_llm

def get_asset_list(state : EntityState):
    storyscript = state['script']
    
    res = entity_chain.invoke({
        "guideline": retrieve_visual_guidelines(
        query=f"""
        Find visual production guidelines relevant to this video story.

        Story:
        {storyscript.model_dump_json(indent=2)}

        Focus on:
        - Visual style
        - Character design
        - Environment design
        - Composition
        - Animation principles
        """,
        k=7
    ),
        "storyscript" : storyscript.model_dump_json(indent=2)
    })
    return{
        "entity" : res
    }


def get_asset_desc(asset : str) -> AssetDesc:
    res =  asset_chain.invoke(
        {
            "asset_name" : asset,
            "guideline": retrieve_visual_guidelines(
                query=f"""
                Find visual production guidelines for designing this asset:

                Asset: {asset}

                Focus on:
                - Shape and proportions
                - Materials and textures
                - Color palette
                - Visual style
                - Modeling or illustration requirements
                - Reusability
                """,
                k=4
            )
        }
    )
    return res

# semaphore = asyncio.Semaphore(5)

# async def limited_asset_desc(asset):
#     async with semaphore:
#         return await get_asset_desc(asset)

def asset_description(state : EntityState):
    assets = state["entity"]

    asset_desc = []

    for asset in assets.environment:
        obj = get_asset_desc(asset)
        asset_desc.append(obj)

    for asset in assets.living_objects:
        obj = get_asset_desc(asset)
        asset_desc.append(obj)

    for asset in assets.non_living_objects:
        obj = get_asset_desc(asset)
        asset_desc.append(obj)

    for asset in assets.extras:
        obj = get_asset_desc(asset)
        asset_desc.append(obj)

    with open("output.json", "w") as file:
        json.dump(
            [asset.model_dump() for asset in asset_desc],
            file,
            indent=4
        )

    return {
        "assets" : asset_desc
    }

    
graph = StateGraph(EntityState)

graph.add_node("entity_list", get_asset_list)
graph.add_node("asset_desc", asset_description)

graph.add_edge(START , "entity_list")
graph.add_edge("entity_list", "asset_desc")
graph.add_edge("asset_desc", END)

get_asset = graph.compile()

