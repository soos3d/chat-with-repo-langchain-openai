import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from ingest import COLLECTION_NAME, require_env

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about a single GitHub repository.

Always call the search_repo tool before answering a question about the code. Search more than once
with different wording when the first result set looks incomplete.

Answer only from the retrieved file contents, and cite the file paths you used. If the repository
does not cover the question, say so plainly instead of guessing."""


def load_retriever(chroma_path, embeddings):
    """Open the persisted vector store and return an MMR retriever over it."""
    if not os.path.isdir(chroma_path):
        raise RuntimeError(
            f"No vector DB found at {chroma_path}. Run `python3 ingest.py` first."
        )

    store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=chroma_path,
    )

    # MMR trades a little relevance for diversity, so answers span several files.
    return store.as_retriever(search_type="mmr", search_kwargs={"k": 6, "fetch_k": 40})


def build_search_tool(retriever):
    """Wrap the retriever in a tool so the agent can decide when to search."""

    @tool
    def search_repo(query: str) -> str:
        """Search the indexed GitHub repository and return the most relevant file excerpts."""
        docs = retriever.invoke(query)
        if not docs:
            return "No matching files found."

        return "\n\n".join(
            f"## {doc.metadata.get('source', 'unknown')}\n{doc.page_content}"
            for doc in docs
        )

    return search_repo


def get_user_input():
    """Get user input and handle the 'quit' command."""
    try:
        question = input("\nPlease enter your question (or 'quit' to stop): ")
    except (EOFError, KeyboardInterrupt):
        return None

    if question.strip().lower() in ("quit", "exit"):
        return None
    return question.strip()


def print_answer(answer, usage):
    """Format and print the answer plus its token usage."""
    print(f"\nAnswer: {answer}\n")
    if usage:
        print(f"Tokens - input: {usage.get('input_tokens')}, output: {usage.get('output_tokens')}")


def main():
    """Interactive REPL over the repository indexed by ingest.py."""
    load_dotenv()

    api_key = require_env("OPENAI_API_KEY")
    language_model = require_env("LANGUAGE_MODEL", "gpt-4o-mini")
    embeddings_model = require_env("EMBEDDINGS_MODEL", "text-embedding-3-small")
    chroma_path = require_env("CHROMA_PATH", "./chroma_db")

    # The embeddings model must match the one used at ingest time.
    embeddings = OpenAIEmbeddings(model=embeddings_model, api_key=api_key)
    retriever = load_retriever(chroma_path, embeddings)

    agent = create_agent(
        model=f"openai:{language_model}",
        tools=[build_search_tool(retriever)],
        system_prompt=SYSTEM_PROMPT,
    )

    print("=" * 100)
    print(f"Chatting with the indexed repo using {language_model}. Type 'quit' to exit.")

    # The full message list is the chat history; the agent reads it on every turn.
    messages = []

    while True:
        question = get_user_input()
        if question is None:
            print("\nBye.")
            break
        if not question:
            continue

        messages.append({"role": "user", "content": question})
        result = agent.invoke({"messages": messages})

        # Keep every message the agent produced, including its tool calls.
        messages = result["messages"]
        final = messages[-1]
        print_answer(final.text, getattr(final, "usage_metadata", None))


if __name__ == "__main__":
    main()
