from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import START, END, StateGraph
from typing import TypedDict, NotRequired
from agents.models import StoryScriptModel
from agents.audio_generation.kokoro_audio import generate_audio

PATH = "/Users/xon/company/Video_Agent/src/agents/audio_generation/output/output.wav"

class AudioState(TypedDict):
    script : StoryScriptModel
    generated_audio_name : NotRequired[str]
    audio_path : NotRequired[str]
    audio_duration : NotRequired[str]

def get_audio(state : AudioState):
        # print(state["script"])
        script = state["script"].script
        audio = generate_audio(script)

        return{
            "generated_audio_name" : audio['filename'],
            "audio_path" : audio['filePath'],
            "audio_duration" : audio['audio_duration']
        }

graph = StateGraph(AudioState)
graph.add_node("generate_audio",get_audio)

graph.add_edge(START, "generate_audio")
graph.add_edge("generate_audio",END)

audio_agent = graph.compile()
    