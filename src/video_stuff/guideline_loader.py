from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import os

load_dotenv()

embeddings = NVIDIAEmbeddings(
    model="nvidia/nemotron-3.5-embed-8b",
    api_key=os.getenv("NVIDIA_API_KEY"),
    dimensions=768
)

vectorstore = Chroma(
    collection_name="guidelines_nemotron_768",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)


def retrieve_visual_guidelines(query: str, k: int = 5) -> str:
    results = vectorstore.similarity_search(
        query,
        k=k
    )

    return "\n\n".join(
        doc.page_content for doc in results
    )
