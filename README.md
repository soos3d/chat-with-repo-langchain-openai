# Chat with a GitHub repo

Ask questions about any public GitHub repository, in plain English, from your terminal.

Point it at a repo, and it clones the code, embeds it, and stores it in a local vector database.
Then you chat with an agent that searches that database whenever it needs to look something up:

```
Please enter your question (or 'quit' to stop): what does the ai-plugin.json manifest configure?

Answer: The `.well-known/ai-plugin.json` manifest declares the plugin's name, description, and
auth mode ("none"), and points to the OpenAPI spec at /openapi.yaml. (.well-known/ai-plugin.json)

Tokens - input: 4821, output: 96
```

Built with [LangChain](https://docs.langchain.com/oss/python/langchain/overview), OpenAI, and
[Chroma](https://www.trychroma.com/).

## Quickstart

You need Python 3.10+, `git`, and an [OpenAI API key](https://platform.openai.com/api-keys).

```sh
git clone https://github.com/soos3d/chat-with-repo-langchain-openai
cd chat-with-repo-langchain-openai

python3 -m venv repo-ai && source repo-ai/bin/activate
pip install -r requirements.txt

cp .env.sample .env      # then add your OPENAI_API_KEY
```

Index a repository:

```sh
python3 ingest.py
# Input the repository you want to index: https://github.com/soos3d/chatgpt-plugin-development-quickstart-express
```

Then chat with it:

```sh
python3 chat.py
```

Type `quit` to exit.

## How it works

Two scripts, one job each.

**`ingest.py` — build the index.**

1. `src/repo_loader.py` shallow-clones the repo into a temp directory and walks it, keeping text
   files and skipping binaries, lockfiles, and `node_modules`. Each file becomes a LangChain
   `Document` tagged with its real path, so answers can cite `src/app.js` rather than a filename
   with no context.
2. `RecursiveCharacterTextSplitter` cuts them into 1000-character chunks with 200 characters of
   overlap, so a function split across a boundary is still readable in both halves.
3. `OpenAIEmbeddings` turns each chunk into a vector, and Chroma persists them to `./chroma_db`.

Nothing is written outside the temp clone and the vector DB. Re-running `ingest.py` rebuilds the
database from scratch — one repo indexed at a time.

**`chat.py` — ask questions.**

This is the interesting part. Instead of a fixed retrieve-then-answer pipeline, the retriever is
wrapped in a *tool* and handed to an agent:

```python
@tool
def search_repo(query: str) -> str:
    """Search the indexed GitHub repository and return the most relevant file excerpts."""
    docs = retriever.invoke(query)
    return "\n\n".join(f"## {d.metadata['source']}\n{d.page_content}" for d in docs)

agent = create_agent(
    model=f"openai:{language_model}",
    tools=[search_repo],
    system_prompt=SYSTEM_PROMPT,
)
```

That one change is what makes this *agentic* RAG. The model decides when to search and what to
search for — so it can rephrase a vague question into a better query, search several times to
gather related files, or answer a follow-up from what it already retrieved. A fixed chain always
runs exactly one search on the raw user question, whether or not that is the right query.

Retrieval uses MMR (maximal marginal relevance), which pulls the top 6 chunks out of 40
candidates while penalizing near-duplicates. On a codebase that matters: a plain similarity search
will happily return six chunks of the same file.

Chat history is just the running list of messages passed back into `agent.invoke()` each turn.

## Configuration

All settings live in `.env`:

| Variable | Description |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key. |
| `LANGUAGE_MODEL` | Chat model used to answer. Defaults to `gpt-4o-mini`. |
| `EMBEDDINGS_MODEL` | Embedding model. Must be the same for `ingest.py` and `chat.py`. |
| `CHROMA_PATH` | Where the local vector DB is written. |
| `FILES_TO_IGNORE` | Comma-separated file names to skip while indexing. |

## Notes

- **Start small.** Indexing is one embedding call per chunk, so a large repo costs real money and
  time. A repo with a few dozen files is a good demo; a monorepo is not.
- **Only public repos.** The clone is unauthenticated.
- **Changing `EMBEDDINGS_MODEL` means re-running `ingest.py`.** Vectors from two different models
  are not comparable, and the search results will be nonsense.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `No vector DB found at ./chroma_db` | Run `python3 ingest.py` first. |
| `OPENAI_API_KEY is not set` | `cp .env.sample .env` and add your key — the code reads `.env`, not `.env.sample`. |
| `git clone failed` | Check the URL is a public repo, in the form `https://github.com/owner/repo`. |
| Answers cite the wrong files | The repo may be too large for 6 chunks of context; raise `k` in `chat.py`. |

## License

Apache 2.0 — see [LICENSE](LICENSE).
