from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict , NotRequired
from langgraph.graph import StateGraph , START, END
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from rich import print
from agents.models import VideoIdea , HighlightOutput
from agents.script_generation.prompt import highlight_prompt

load_dotenv()

llm = ChatGoogleGenerativeAI(model = 'gemini-3.5-flash-lite', temperature = 0.5)
highlight_llm = llm.with_structured_output(HighlightOutput)

class ScriptState(TypedDict):
    idea :  VideoIdea
    highlights : NotRequired[HighlightOutput]
    selected_highlight : NotRequired[int]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system" , highlight_prompt),
        ("human" , """
        Idea : {idea}

        Generate the highlights for this idea.  
    """)
    ]
)

highlight_chain = prompt | highlight_llm

def generate_highlights(state : ScriptState):

    res = highlight_chain.invoke({
        "idea" : state.get('idea').model_dump_json(indent = 2)
    })

    return{
        "highlights" : res
    }


graph = StateGraph(ScriptState)

graph.add_node("generate_highlights" , generate_highlights)

graph.add_edge(START , "generate_highlights")
graph.add_edge("generate_highlights",END)

script_agent = graph.compile()
