import os
import shutil

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.repo_loader import get_files_to_ignore, load_repo

COLLECTION_NAME = "repo"


def require_env(name, default=None):
    """Read an env var, failing fast with an actionable message when it is missing."""
    value = os.getenv(name, default)
    if not value:
        raise RuntimeError(f"{name} is not set. Copy .env.sample to .env and fill it in.")
    return value


def build_vector_db(chunks, embeddings, chroma_path):
    """Rebuild the Chroma store from scratch with the given chunks."""
    # A run always rebuilds: one repo indexed at a time keeps the demo predictable.
    if os.path.isdir(chroma_path):
        print(f"Removing the existing vector DB at {chroma_path}...")
        shutil.rmtree(chroma_path)

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=chroma_path,
    )


def main():
    """Clone a public GitHub repo, embed its files, and persist them to a local Chroma DB."""
    load_dotenv()

    api_key = require_env("OPENAI_API_KEY")
    embeddings_model = require_env("EMBEDDINGS_MODEL", "text-embedding-3-small")
    chroma_path = require_env("CHROMA_PATH", "./chroma_db")

    repo_url = input("Input the repository you want to index: ")

    # Clone the repo and read every text file into a Document.
    print("=" * 100)
    docs = load_repo(repo_url, files_to_ignore=get_files_to_ignore())

    # Split into chunks small enough to retrieve, with enough overlap to keep code readable.
    print("=" * 100)
    print("Splitting documents...")
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    print(f"Generated {len(chunks)} chunks.")

    # Embed the chunks and write them to the local vector store.
    print("=" * 100)
    print(f"Embedding with {embeddings_model} and building the vector DB...")
    embeddings = OpenAIEmbeddings(model=embeddings_model, api_key=api_key)
    build_vector_db(chunks, embeddings, chroma_path)

    print("=" * 100)
    print(f"Vector DB written to {chroma_path}. Run `python3 chat.py` to ask questions.")


if __name__ == "__main__":
    main()
