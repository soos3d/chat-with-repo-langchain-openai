import os
import shutil
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

from langchain_core.documents import Document

# Directories that never contain useful source, skipped during the walk.
SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build",
    ".next", ".cache", "vendor", "target", ".idea", ".vscode",
}

# Extensions we consider readable source/docs/config. Everything else is skipped.
TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".rb", ".java", ".kt",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".swift", ".sh", ".sql", ".sol",
    ".md", ".mdx", ".rst", ".txt", ".json", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".env", ".html", ".css", ".scss", ".graphql", ".proto",
}

# Files without an extension that are still worth indexing.
TEXT_FILENAMES = {"Dockerfile", "Makefile", "Procfile", "LICENSE", "README"}

MAX_FILE_BYTES = 500_000  # Skip anything larger; usually generated or minified.


def parse_repo_url(repo_url):
    """Validate a GitHub URL and return (owner, repo)."""
    parsed = urllib.parse.urlparse(repo_url.strip())
    parts = [p for p in parsed.path.split("/") if p]

    if parsed.scheme not in ("http", "https") or len(parts) < 2:
        raise ValueError(
            f"Not a valid repository URL: {repo_url!r}. "
            "Expected something like https://github.com/owner/repo"
        )

    owner, repo = parts[0], parts[1]
    return owner, repo.removesuffix(".git")


def is_text_file(path, files_to_ignore):
    """Return True if the file looks like indexable text."""
    if path.name in files_to_ignore:
        return False

    if path.stat().st_size > MAX_FILE_BYTES:
        return False

    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in TEXT_FILENAMES


def read_repo_files(repo_root, repo_url, files_to_ignore):
    """Walk a cloned repo and turn every text file into a Document."""
    docs = []

    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(repo_root)

        # Skip anything living under a noisy directory.
        if SKIP_DIRS.intersection(relative_path.parts):
            continue

        if not is_text_file(path, files_to_ignore):
            continue

        # Binary files sneak past the extension check, so decoding is the real test.
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if not content.strip():
            continue

        docs.append(Document(
            page_content=f"File: {relative_path}\n\n{content}",
            metadata={"source": str(relative_path), "repo": repo_url},
        ))

    return docs


def load_repo(repo_url, files_to_ignore=None):
    """Shallow-clone a public GitHub repo and return its text files as Documents."""
    owner, repo = parse_repo_url(repo_url)
    files_to_ignore = files_to_ignore or set()

    if shutil.which("git") is None:
        raise RuntimeError("git is not installed or not on PATH; it is required to clone the repo.")

    # Clone into a temp dir; nothing is written to the project directory.
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Cloning {owner}/{repo}...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--quiet", repo_url, tmpdir],
            capture_output=True,
            text=True,
        )

        # Fail loudly: a clone that produces nothing must not look like success.
        if result.returncode != 0:
            raise RuntimeError(f"git clone failed for {repo_url}:\n{result.stderr.strip()}")

        docs = read_repo_files(Path(tmpdir), repo_url, files_to_ignore)

    if not docs:
        raise RuntimeError(f"No indexable text files found in {repo_url}.")

    print(f"Read {len(docs)} files from {owner}/{repo}.")
    return docs


def get_files_to_ignore():
    """Read the comma-separated FILES_TO_IGNORE env var into a set."""
    raw = os.getenv("FILES_TO_IGNORE", "")
    return {name.strip() for name in raw.split(",") if name.strip()}
