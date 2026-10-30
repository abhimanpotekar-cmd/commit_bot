# Commit Bot 🤖

Commit Bot is a terminal CLI tool that helps developers write better Git commit messages using a local Ollama language model.

It examines your staged Git changes and recent commit history to generate **three** relevant, conventional commit-message suggestions matching your project's commit style. Rather than committing automatically, it provides an interactive terminal workflow allowing you to review, regenerate, select, and edit the final commit message.

It also supports **GitHub Pull Requests**, allowing you to generate squash or merge commit messages directly from any public or authenticated GitHub PR URL.

---

## ✨ Features

- **Local & Private**: Runs completely locally using Ollama (`qwen3:1.7b` by default via `langchain-ollama`). Your code never leaves your machine.
- **Terminal Review Workflow**: Displays 3 alternative suggestions in a Rich table. You can regenerate new suggestions, choose your favorite, or edit the title and body interactively.
- **Style-Aware**: Reads recent repository commit titles to match your capitalization, prefix conventions (e.g. `feat:`, `fix:`), and imperative style.
- **Smart Diff Chunking & Summarization**: Automatically splits large file diffs at hunk boundaries (`@@ `) and summarizes them before message generation.
- **Privacy Exclusions**: Excludes sensitive patterns by default (`.env`, `*.key`, `*.pem`, `uv.lock`, `package-lock.json`).
- **GitHub Pull Request Integration**: Fetch and synthesize unified diffs directly from GitHub pull request URLs (`commitbot pr <url>`).

---

## 📋 Prerequisites

1. **Python**: `3.11` or higher
2. **Git**: Installed and available on your system `PATH`
3. **Ollama**: Installed and running locally
   ```bash
   ollama run qwen3:1.7b
   ```

---

## 🚀 Installation & Setup

### Option 1: Direct Install via `uv` (Recommended — no cloning needed)
If you have `uv` installed, install Commit Bot globally in one command:

```bash
uv tool install git+https://github.com/abhimanpotekar-cmd/commit_bot.git
```

### Option 2: Install from Source
1. Clone the repository:
   ```bash
   git clone https://github.com/abhimanpotekar-cmd/commit_bot.git
   cd commit-bot
   ```

2. Install globally as a CLI tool:
   ```bash
   uv tool install .
   ```
   *(Or for local development: `uv sync` or `pip install -e .`)*

3. Verify installation:
   ```bash
   commitbot --help
   ```
   
## ⚙️ Configuration

Commit Bot works out of the box with sensible defaults. To customize settings, copy the example configuration file:

```bash
cp commitbot.example.toml commitbot.toml
```

*(Note: `commitbot.toml` is gitignored to keep your local preferences private.)*

### Available Settings (`commitbot.toml`):
```toml
# Installed Ollama model name
model = "qwen3:1.7b"

# Local Ollama endpoint
base_url = "http://localhost:11434"

# Temperature (0.0 = deterministic, 1.0 = creative)
temperature = 0.23

# Request timeout in seconds
request_timeout = 120.0

# Number of recent commit titles used as writing-style examples
history_limit = 10

# Max character limit before triggering diff summarization
max_diff_chars = 12000

# File patterns excluded from model context
exclude_patterns = [
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "uv.lock",
    "package-lock.json"
]
```

### GitHub Authentication (Optional):
For private repositories or to avoid GitHub API rate limits, set your personal access token in `.env`:
```env
GITHUB_TOKEN=ghp_your_github_personal_access_token
```

---

## 💻 Usage

### 1. Local Staged Commits
Stage your desired changes, then run:

```bash
git add .
commitbot bot
```
*(You can also run `commitbot suggest` or `python main.py bot`)*

**Workflow:**
1. A table displaying 3 alternative commit suggestions will appear.
2. Prompt: `Generate new suggestions? [y/N]`
3. Prompt: `Select the commit message [1/2/3]:`
4. Prompt: `Edit this message [y/N]:` (allows tweaking title and body)
5. The final selected message is printed to stdout ready to be copied or piped into `git commit -m`.

---

### 2. GitHub Pull Requests
Generate commit suggestions for a pull request by providing its URL:

```bash
commitbot pr https://github.com/owner/repository/pull/12
```

Commit Bot will fetch the PR metadata, filter excluded files, download the patches, retrieve the base repository's recent commit history, and generate 3 suggestions.

---

## 🧪 Running Tests

Run the full pytest suite:

```bash
pytest
```

Run tests by module:
```bash
pytest tests/test_local_git.py tests/test_history.py    # Local git operations
pytest tests/test_processing.py                          # Filters, chunking, context
pytest tests/test_github.py                              # GitHub PR parsing and mocking
pytest tests/test_generation.py                          # Prompt loading and validation
pytest tests/test_cli.py                                 # Typer CLI workflows
```