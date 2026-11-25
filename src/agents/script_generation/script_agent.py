from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict , NotRequired, Literal
from langgraph.graph import StateGraph , START, END
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from rich import print
from agents.models import VideoIdea , HighlightOutput, HighlightEvaluationModelBatch , HighlightEvaluationModel, Highlight , StoryScriptModel
from agents.script_generation.prompt import highlight_prompt, eval_prompt, script_generation_prompt
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
import os


load_dotenv()

# llm = ChatOpenAI(
#     model="local-model",
#     base_url="http://localhost:1235/v1",
#     api_key="lm-studio",
#     temperature=0.8,
# )

# llm_eval = ChatOpenAI(
#     model="local-model",
#     base_url="http://localhost:1235/v1",
#     api_key="lm-studio",
#     temperature=0.1,
# )
# llm = ChatNVIDIA(
#   model="nvidia/nemotron-3.5-lightning-30b-a3b",
#   api_key=os.getenv("NVIDIA_API_KEY"), 
#   temperature=0.8,
#   top_p=0.95,
#   max_tokens=16384
# )
# llm_eval = ChatNVIDIA(
#   model="nvidia/nemotron-3.5-lightning-30b-a3b",
#   api_key=os.getenv("NVIDIA_API_KEY"), 
#   temperature=0.8,
#   top_p=0.95,
#   max_tokens=16384
# )
llm = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite', temperature = 0.8)
# llm = ChatGroq(model="openai/gpt-oss-120b" , temperature=0.8 , max_tokens=15000)
# llm = primary_llm.with_fallbacks([fallback_llm, fallback_llm_2])

# fallback_llm = ChatGroq(model="gpt-oss-120b" , temperature=0.8)
# fallback_llm_2 = ChatGroq(model="gpt-oss-20b" , temperature=0.8)

# llm_eval = ChatNVIDIA(model="nvidia/nemotron-3.5-lightning-30b-a3b", temperature=0.1, max_tokens=16384)
llm_eval = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite', temperature = 0.1)
# llm_eval = ChatGroq(model="openai/gpt-oss-120b" , temperature=0.1 , max_tokens=15000)

highlight_llm = llm.with_structured_output(HighlightOutput, strict=True)
eval_llm = llm_eval.with_structured_output(HighlightEvaluationModelBatch, strict=True)
script_llm = llm.with_structured_output(StoryScriptModel, strict=True)

config = {
    "configurable" : {
        "thread_id" : "thread-1"
    }
}

class ScriptState(TypedDict):
    idea :  VideoIdea
    highlights : NotRequired[HighlightOutput]
    evaluated_highlights : NotRequired[HighlightEvaluationModelBatch]
    selected_highlight : NotRequired[list[HighlightEvaluationModel]]
    approved_highlight_id : NotRequired[int]
    approved_highlight : NotRequired[Highlight]
    script : NotRequired[StoryScriptModel]
    approved_script : NotRequired[bool]


prompt = ChatPromptTemplate.from_messages([
    ("system", highlight_prompt),
    ("human", """
    ORIGINAL VIDEO IDEA:

    {idea}

    Generate 3-7 narrative highlights.

    IMPORTANT:
    - Every highlight must directly support the original idea.
    - Do not introduce an unrelated secondary topic.
    - Every highlight must contribute to the central narrative.
    - Explain the connection to the original idea.
    - The highlights together must form one coherent narrative arc.
    """)
])
eval_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", eval_prompt),
        ('human' , """
            Highlights : {highlights}

            these are the script highlights please evalute them.
            """)
        ]
)

script_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", script_generation_prompt ),
        ("human" , """
        Here is the 
        Idea : {idea} , 
        Highlight : {approved_highlight}
        
        your task is to generate the script for the above idea and highlight""")
    ]
) 
highlight_chain = prompt | highlight_llm
evaluation_chain = eval_prompt | eval_llm
script_chain =  script_prompt | script_llm

def generate_highlights(state : ScriptState):
    
    res = highlight_chain.invoke({
        "idea" : state.get('idea')
    })

    return{
        "highlights" : res
    }

def validate_highlights(state : ScriptState):

    res = evaluation_chain.invoke({
        "highlights" : state.get('highlights').model_dump_json(indent=2)
    })

    return{
        "evaluated_highlights" : res
    }

def select_best_highlight(state : ScriptState):
    print(state)
    highlights_data = state['highlights']
    highlights = (
        highlights_data["highlights"]
        if isinstance(highlights_data, dict)
        else highlights_data.highlights
    )
    evaluated_batch = state["evaluated_highlights"]

    if isinstance(evaluated_batch, dict):
        evaluated_highlights = evaluated_batch["evaluated_highlights"]
    else:
        evaluated_highlights = evaluated_batch.evaluated_highlights
    # print(evaluated_highlights)
    # print(highlights)
    selected_highlights = []
    for evaluated in evaluated_highlights:
        score = evaluated["overall_score"] if isinstance(evaluated, dict) else evaluated.overall_score
        evaluation_id = evaluated["id"] if isinstance(evaluated, dict) else evaluated.id

        if score >= 8:
            for highlight in highlights:
                highlight_id = highlight["id"] if isinstance(highlight, dict) else highlight.id
                if evaluation_id == highlight_id:
                    selected_highlights.append(highlight)

    return{
        "selected_highlight" : selected_highlights
    }

def router(state : ScriptState): 
    selected_highlights = state["selected_highlight"]

    if selected_highlights:
        return "hitl_highlight_selection"
    else: 
        return "END"

def script_router(state : ScriptState):
    script = state['script']

    if script:
        return "hitl_script"
    else: 
        return "END"    


def hitl_highlight_selection(state: ScriptState):
    selected_highlights = state["selected_highlight"]
    print(state)
    evaluated_batch = state["evaluated_highlights"]

    evaluated_highlights = (
        evaluated_batch["evaluated_highlights"]
        if isinstance(evaluated_batch, dict)
        else evaluated_batch.evaluated_highlights
    )



    # Create a lookup for evaluation scores using highlight IDs
    evaluation_map = {
        (evaluation["id"] if isinstance(evaluation, dict) else evaluation.id):
        (evaluation["overall_score"] if isinstance(evaluation, dict) else evaluation.overall_score)
        for evaluation in evaluated_highlights
    }

    # Prepare highlights for human selection
    highlights_for_review = [
        {
            "id": highlight.id,
            "title": highlight.title,
            "description": highlight.description,
            "narrative_purpose": highlight.narrative_purpose,
            "visual_description": highlight.visual_description,
            "overall_score": evaluation_map.get(highlight.id)
        }
        for highlight in selected_highlights
    ]

    decision = interrupt({
        "message": "Choose one of the following highlights to turn into a script.",
        "highlights": highlights_for_review
    })

    # Validate the user's selection
    approved_highlight_id = decision["approved_highlight_id"]

    approved_highlight = next(
        (
            highlight
            for highlight in selected_highlights
            if highlight.id == approved_highlight_id
        ),
        None
    )

    if approved_highlight is None:
        raise ValueError(
            f"Invalid highlight ID: {approved_highlight_id}"
        )

    return {
        "approved_highlight_id": approved_highlight_id,
        "approved_highlight": approved_highlight
    }

def hitl_script(state: ScriptState):
    script = state["script"]

    decision = interrupt({
        "message": "Please verify the generated script",
        "script": script.model_dump()
    })

    approved_script = decision["approved_script"]

    if isinstance(approved_script, bool):
        approved = approved_script
    elif isinstance(approved_script, str):
        approved = approved_script.strip().lower() in ("y", "yes")
    else:
        raise ValueError("Approval must be a boolean or string")

    return {
        "approved_script": approved
    }

def genarate_script(state : ScriptState):

    res = script_chain.invoke({
        "idea" : state.get('idea'),
        "approved_highlight" : state.get('approved_highlight').model_dump_json(indent= 2) 
    })
    return {
        "script" : res

    }
graph = StateGraph(ScriptState)

graph.add_node("generate_highlights" , generate_highlights)
graph.add_node("validate_highlights", validate_highlights)
graph.add_node("select_best_highlight" , select_best_highlight)
graph.add_node("hitl_highlight_selection" , hitl_highlight_selection)
graph.add_node("genarate_script" , genarate_script)
graph.add_node("hitl_script" , hitl_script)

graph.add_edge(START , "generate_highlights")
graph.add_edge("generate_highlights","validate_highlights")
graph.add_edge("validate_highlights", "select_best_highlight")
graph.add_conditional_edges("select_best_highlight" , router ,{
    "hitl_highlight_selection" : "hitl_highlight_selection",
    "END" : END
})
graph.add_edge("hitl_highlight_selection" , "genarate_script")
graph.add_conditional_edges("genarate_script" , script_router ,{
    "hitl_script" : "hitl_script",
    "END" : END
})
graph.add_edge("hitl_script", END)


script_agent = graph.compile()

