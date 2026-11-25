from pathlib import Path
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import time
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import os
load_dotenv()

# embeddings = GoogleGenerativeAIEmbeddings(
#     model="gemini-embedding-2",
#     output_dimensionality=768,
#     max_retries=5
# )
embeddings = NVIDIAEmbeddings(
    model="nvidia/nemotron-3.5-embed-8b",
    api_key= os.getenv("NVIDIA_API_KEY"),
    dimensions=768
  )

GUIDELINES_DIR = Path("guideline.txt")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

with open(GUIDELINES_DIR, "r", encoding="utf-8") as file:
    text = file.read()

chunks = splitter.split_text(text)

vectorstore = Chroma(
    collection_name="guidelines",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)


batch_size = 50

for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]

    vectorstore.add_texts(batch)

    print(f"Inserted {min(i + batch_size, len(chunks))}/{len(chunks)}")

    time.sleep(10)
    time.sleep(2)

print("Done!")

