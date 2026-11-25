from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict , NotRequired
from agents.models import VideoIdea , IdeaModel , IdeaEvaluationBatch
from agents.ideation.prompts import generation_prompt, idea_reference, evaluator_prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END , START
from langgraph.types import interrupt
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
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

# judge_llm = ChatOpenAI(
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
# llm = ChatNVIDIA(model="nvidia/nemotron-3.5-lightning-30b-a3b", temperature=0.8, max_tokens=16384)
# llm = ChatGroq(model="openai/gpt-oss-120b" , temperature=0.8 , max_tokens=15000)
llm = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite', temperature = 0.8)
# llm = primary_llm.with_fallbacks([fallback_llm, fallback_llm_2])

# fallback_llm = ChatGroq(model="gpt-oss-120b" , temperature=0.8)
# fallback_llm_2 = ChatGroq(model="gpt-oss-20b" , temperature=0.8)

# judge_llm = ChatNVIDIA(model="nvidia/nemotron-3.5-lightning-30b-a3b", temperature=0.1, max_tokens=16384)
judge_llm = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite' ,temperature = 0.1)
# judge_llm = ChatGroq(model="openai/gpt-oss-120b" , temperature=0.1, max_tokens=15000)
# judge_llm = ChatNVIDIA(
#   model="nvidia/nemotron-3.5-lightning-30b-a3b",
#   api_key=os.getenv("NVIDIA_API_KEY"), 
#   temperature=0.8,
#   top_p=0.95,
#   max_tokens=16384
# )

llm_structured = llm.with_structured_output(IdeaModel, strict=True)
llm_judge = judge_llm.with_structured_output(IdeaEvaluationBatch, strict=True)
checkpointer = MemorySaver()
config = {
    "configurable" : {
        "thread_id" : "thread-1"
    }
}

class IdeaState(TypedDict):
    topic : str | None 
    ideas : NotRequired[IdeaModel]
    reviewed_ideas : NotRequired[IdeaEvaluationBatch]
    selected_ideas : NotRequired[list[VideoIdea]]
    approved_idea_id : NotRequired[int]
    approved_idea : NotRequired[VideoIdea]

prompt = ChatPromptTemplate.from_messages([
    ("system", generation_prompt) , 
    ("human" ,"""
        Topic: {topic}

        Reference Ideas:
        {idea_references}

        Additional Context:
        {additional_context}

        Generate exactly 5 original video ideas.
        """)
    ])

review_prompt = ChatPromptTemplate.from_messages([
    ("system", evaluator_prompt),
    ("human", """
Evaluate the following batch of ideas:

{ideas}

Rate every idea independently and return the structured evaluation.
""")
])

chain = prompt | llm_structured

review_chain = review_prompt | llm_judge

def idea_generation(state : IdeaState):
    res = chain.invoke({
        "topic" : state.get("topic") or "None", 
        "idea_references" : idea_reference,
        "additional_context" : None
    })

    return{
        "ideas" : res
    }

def idea_selection(state : IdeaState):
    
    ideas = state["ideas"]
    reviewed_ideas = review_chain.invoke({
            "ideas": ideas.model_dump_json(indent=2)
        })
    return{
        "reviewed_ideas" : reviewed_ideas
    }

def get_selected_ideas(state : IdeaState):
    evaluations = state["reviewed_ideas"].evaluated_ideas
    ideas = state["ideas"].ideas

    selected_ideas = []

    for evaluation in evaluations:
        if evaluation.overall_score >= 8:
            for idea in ideas:
                if evaluation.idea_id == idea.id:
                    selected_ideas.append(idea)

    return {
        "selected_ideas" : selected_ideas
        }

def route_to_the_hitl(state : IdeaState):
    ideas = state['selected_ideas']

    if ideas:
        return "human_approval"
    else:
        return "END"    

def human_approval(state : IdeaState):
    selected_ideas = state['selected_ideas']
    decision = interrupt({
        "message" : "These are the ShortListed ideas. Select one of the following ideas: ",
        "ideas" : [{
                            "idea" : idea.id,
                            "title" : idea.title,
                            "category" : idea.category,
                            "concept" : idea.concept,
                            "hook" : idea.hook
                         } for idea in selected_ideas
                 ]
    })

    approved_id = decision["approved_idea_id"]
    approved_idea = next(
        (
            idea for idea in selected_ideas
            if idea.id == approved_id
        ),
        None
    )
    if approved_idea is None:
        raise ValueError(f"Invalid idea ID: {approved_id}")

    return {
        "approved_idea_id": approved_id,
        "approved_idea": approved_idea
    }

graph = StateGraph(IdeaState)

graph.add_node("idea_generation" , idea_generation)
graph.add_node("idea_selection", idea_selection)
graph.add_node("human_approval" , human_approval)
graph.add_node("get_selected_ideas",get_selected_ideas)

graph.add_edge(START,"idea_generation")
graph.add_edge("idea_generation", "idea_selection")
graph.add_edge("idea_selection", "get_selected_ideas" )
graph.add_conditional_edges("get_selected_ideas",route_to_the_hitl, {
    "human_approval" : "human_approval",
    "END" : END
})
graph.add_edge("human_approval", END)

idea_generation_agent = graph.compile(checkpointer=checkpointer)
