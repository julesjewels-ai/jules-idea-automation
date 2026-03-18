# Jules Idea Automation

<div align="center">
  <img src="assets/jules_hero_banner.png" alt="Jules Idea Automation — from spark to PR in one command" width="100%">
</div>

<br>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![Code Quality: Ruff](https://img.shields.io/badge/code%20quality-ruff-blueviolet.svg)](https://docs.astral.sh/ruff/)
[![Type Checking: mypy](https://img.shields.io/badge/type%20checking-mypy-blue.svg)](https://mypy-lang.org/)

An **Idea Factory** CLI that automates the full journey from _raw concept_ to a _developer-ready GitHub repository_ with a Jules AI session attached — in a single command.

---

## Table of Contents

- [Key Features](#key-features)
- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Usage](#usage)
  - [Interactive Guide](#interactive-guide)
  - [Agent Mode](#-agent-mode)
  - [Website Mode](#-website-mode)
  - [Paste Mode](#-paste-mode)
  - [Manual Mode](#-manual-mode)
  - [Status & Sources](#status--sources)
  - [CLI Reference](#cli-reference)
- [Documentation](#documentation)
  - [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Available Commands](#available-commands)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Key Features

- **Four Input Modes** — AI-generated ideas (_Agent_), website extraction (_Website_), paste content directly (_Paste_), or bring-your-own concept (_Manual_).
- **Category-Aware Ideation** — Target specific categories like `cli_tool`, `web_app`, `api_service`, `mobile_app`, `automation`, or `ai_ml`.
- **Full MVP Scaffolding** — Generates a 9-file SOLID-compliant project structure (entry point, source packages, tests, Makefile, `.env.example`, `.gitignore`) in a single atomic Git commit via the GitHub Git Data API.
- **Thinking Mode** — Leverages Gemini's `ThinkingConfig` for transparent, deep-thought rationales during idea generation.
- **Jules Session Orchestration** — Automatically waits for repository indexing and initialises an `AUTO_CREATE_PR` session so the Jules agent starts working immediately.
- **Session Monitoring** — Live-poll sessions with `--watch` to see real-time activity and PR outputs.
- **API Response Caching** — File-based cache in `.cache/` reduces Gemini latency and cost on repeated queries.
- **Audit Logging** — Every workflow execution is persisted to `.jules_history.jsonl` via an Event Bus, giving you a full history of generated ideas and sessions.
- **Resilient Generation** — Exponential backoff retries plus a comprehensive fallback scaffold if API calls time out.

---

## How It Works

```mermaid
flowchart TD
    A[Input Modes] --> B{Jules CLI}

    subgraph Input Sources
    A1(Agent: AI Generation) -.-> A
    A2(Website: Extraction) -.-> A
    A4(Paste: Direct Content) -.-> A
    A3(Manual: Custom Ideas) -.-> A
    end

    B --> C[Draft Project Specifications]
    C --> D[Create GitHub Repository]
    D --> E[Wait for Source Indexing]
    E --> F[Initialize Jules Session]

    B -.-> G[(Local Audit Log)]

    style B fill:#6366f1,stroke:#3730a3,stroke-width:2px,color:#fff
    style A1 fill:#e0e7ff,stroke:#4f46e5,color:#333
    style A2 fill:#dbeafe,stroke:#2563eb,color:#333
    style A3 fill:#dcfce7,stroke:#16a34a,color:#333
```

1. **Idea Generation** — You provide a prompt, category, URL, or title. The CLI uses `GeminiClient` to produce a structured idea (title, description, tech stack, features).
2. **Repository Scaffolding** — `GitHubClient` creates a GitHub repo and pushes an MVP scaffold as a single atomic commit using the Git Data (Blobs → Tree → Commit → Ref) API.
3. **Source Indexing** — The CLI polls the Jules API until the new repository is discovered and indexed (default timeout: 120 s, 10 s intervals).
4. **Session Start** — `JulesClient` creates an `AUTO_CREATE_PR` session linked to the repository so the Jules agent begins development immediately.
5. **Optional Watch** — Pass `--watch` to live-poll the session until the PR is created or the timeout expires.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.12+ |
| **AI** | Google Gemini (`google-genai` SDK, `v1beta` API) |
| **VCS** | GitHub REST & Git Data API via `requests` |
| **Session Orchestration** | Jules API (`v1alpha/sessions`) |
| **Web Scraping** | BeautifulSoup 4 |
| **Data Models** | Pydantic 2.x |
| **Configuration** | `python-dotenv` |
| **Linting / Formatting** | Ruff (lint + format) |
| **Type Checking** | mypy (strict mode with Pydantic plugin) |
| **Testing** | pytest + pytest-mock + pytest-cov |

---

## Prerequisites

Before you begin, make sure you have:

- **Python 3.12 or higher** — the project uses 3.12+ features and type hints. Check with `python3 --version`.
- **pip** — Python package manager (bundled with Python 3).
- **Git** — for cloning the repository.
- **API Keys** — you will need three keys (see [Environment Variables](#environment-variables)):
  - A **Google Gemini API key** — [get one here](https://aistudio.google.com/apikey).
  - A **GitHub Personal Access Token** with `repo` scope — [create one here](https://github.com/settings/tokens).
  - A **Jules API key** — available from the Jules console.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/julesjewels-ai/jules-idea-automation.git
cd jules-idea-automation
```

### 2. Create a Virtual Environment

```bash
python3.12 -m venv venv
source venv/bin/activate  # macOS / Linux
# On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all runtime _and_ development dependencies (Ruff, mypy, pytest, etc.).

### 4. Configure Environment Variables

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

Open `.env` in your editor and set:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here
JULES_API_KEY=your_jules_api_key_here
```

> **Note:** The `.env` file is listed in `.gitignore` and will never be committed.

### 5. Verify the Installation

```bash
python main.py guide
```

If everything is configured correctly, you'll see the interactive user guide.

---

## Usage

### Interactive Guide

New to the tool? Start here:

```bash
# Show the main welcome guide
python main.py guide

# Show a specific workflow tutorial
python main.py guide --workflow agent
python main.py guide --workflow website
python main.py guide --workflow manual
```

### 🤖 Agent Mode

Let Gemini AI generate ideas from scratch.

<img src="assets/agent_mode_icon.png" alt="Agent Mode" width="100%" />

```bash
# Generate a random idea
python main.py agent

# Target a specific category
python main.py agent --category cli_tool

# Generate and watch until PR is created
python main.py agent --category web_app --watch

# Create a private repository
python main.py agent --private
```

Available categories: `web_app`, `cli_tool`, `api_service`, `mobile_app`, `automation`, `ai_ml`.

### 🌐 Website Mode

Scrape a website and generate a prototype idea from its content.

<img src="assets/website_mode_icon.png" alt="Website Mode" width="100%" />

```bash
# Extract an idea from a website
python main.py website --url https://example.com

# Watch session until completion
python main.py website --url https://example.com --watch

# Skip the scraper — provide page content directly
python main.py website --content "A finance app that builds money habits in three minutes a day..."
```

The scraper includes content validation that enforces minimum text length and detects blocked/login-restricted pages to prevent hallucinated ideas from invalid sources. If scraping is blocked, use `--content` to provide the page text directly, or use the **Paste Mode** below.

### 📋 Paste Mode

Paste or pipe content directly — bypasses the web scraper entirely. Ideal when corporate firewalls block URL scraping or you've already copied the text.

```bash
# Auto-read from clipboard (recommended)
python main.py paste --clipboard

# Read from a text file
python main.py paste --file page.txt

# Pipe from stdin
cat page.html | python main.py paste -

# Interactive paste (Cmd+V, then type END to submit)
python main.py paste
```

All input methods show a content preview (character count + first 200 chars) before Gemini starts processing, so you can confirm the right content was captured.

### ✍️ Manual Mode

Bring your own idea — provide title and optional metadata.

<img src="assets/manual_mode_icon.png" alt="Manual Mode" width="100%" />

```bash
# Basic manual entry (slug auto-generated from title)
python main.py manual "My Awesome Tool"

# Full manual entry with all options
python main.py manual "Task Manager" \
  --description "A CLI tool for managing daily tasks with priority tags" \
  --slug my-task-cli \
  --tech_stack "Python,Click,SQLite" \
  --features "CRUD operations,Priority tags,Export CSV" \
  --watch
```

### Status & Sources

```bash
# Check session status
python main.py status <session_id>

# Watch an existing session in real time
python main.py status <session_id> --watch

# List available indexed sources
python main.py list-sources
```

### CLI Reference

| Flag | Description | Default |
|---|---|---|
| `--category` | Target a specific idea category (Agent mode) | None (random) |
| `--description` | Detailed description for Manual mode | Uses title |
| `--slug` | Custom GitHub repository slug | Auto-slugified title |
| `--url` | Target URL for Website mode | *(required)* |
| `--content` | Provide page text directly, skipping the scraper (Website mode) | None |
| `--clipboard` | Auto-read content from clipboard (Paste mode) | `False` |
| `--file` | Read content from a text file (Paste mode) | None |
| `--tech_stack` | Comma-separated list of technologies | `[]` |
| `--features` | Comma-separated list of MVP features | `[]` |
| `--private` | Create a private repository | `False` |
| `--timeout` | Timeout in seconds for indexing/watching | `1800` |
| `--watch` | Live-poll session until completion or timeout | `False` |

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | SOLID principles, Dependency Injection, Event Bus, Gemini API Caching |
| [Development Log](docs/DEVLOG.md) | Chronological history of changes and decisions |
| [Roadmap](docs/ROADMAP.md) | Planned features and future direction |
| [Contributing](CONTRIBUTING.md) | Setup, code style, PR process |

### Project Structure

```
jules-idea-automation/
├── main.py                          # Entry point — orchestration only
├── pyproject.toml                   # Project metadata, Ruff, mypy, pytest config
├── requirements.in                  # Direct dependencies (pip-compile input)
├── requirements.txt                 # Locked dependencies (pip-compile output)
├── .env.example                     # Template for required environment variables
├── .jules_history.jsonl             # Audit log of workflow executions
├── .cache/                          # File-based Gemini API response cache
│
├── src/
│   ├── cli/                         # Argument parsing, command handlers
│   ├── core/                        # Workflow orchestrator, Pydantic models, events
│   ├── services/                    # Gemini, GitHub, Jules, Scraper, Cache, Event Bus
│   ├── templates/                   # Project scaffolding templates
│   └── utils/                       # Errors, polling, reporter, security, slugify
│
├── tests/                           # Test suite (mirrors src/ structure)
├── docs/                            # Architecture, devlog, roadmap
└── assets/                          # Images for README
```

---

## Environment Variables

### Required

| Variable | Description | How to Get |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for idea + scaffold generation | [Google AI Studio](https://aistudio.google.com/apikey) |
| `GITHUB_TOKEN` | GitHub Personal Access Token with `repo` scope | [GitHub Settings → Tokens](https://github.com/settings/tokens) |
| `JULES_API_KEY` | Jules API key for session creation and monitoring | Jules Console |

All three are loaded automatically from `.env` via `python-dotenv`.

> **Security:** The CLI verifies that `.gitignore` blocks `.env` before any push operation to prevent accidental credential exposure.

---

## Available Commands

| Command | Description |
|---|---|
| `python main.py guide` | Interactive getting-started tutorial |
| `python main.py agent` | Generate an AI idea and create a repo |
| `python main.py website --url <URL>` | Extract idea from a website |
| `python main.py website --content "..."` | Extract idea from provided text (no scraping) |
| `python main.py paste --clipboard` | Extract idea from clipboard content |
| `python main.py paste --file <path>` | Extract idea from a text file |
| `python main.py paste` | Interactive paste mode |
| `python main.py manual "<title>"` | Create a repo from your own idea |
| `python main.py status <session_id>` | Check or watch an existing session |
| `python main.py list-sources` | List indexed sources in Jules |
| `python -m pytest tests/ -v` | Run full test suite |
| `ruff check src/ tests/` | Lint all source and test files |

---

## Testing

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Run a specific test file
python -m pytest tests/services/test_gemini.py -v
```

The `tests/` directory mirrors `src/` with unit, integration, and template tests. All service dependencies use Protocol-based interfaces, so tests inject mocks via `pytest-mock`.

---

## Troubleshooting

### Missing API Keys

**Error:** `Configuration Error: GEMINI_API_KEY is not set`

**Fix:**
1. Ensure `.env` exists in the project root: `cp .env.example .env`
2. Fill in all three keys (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `JULES_API_KEY`).
3. Keys are loaded at startup by `python-dotenv` — no restart required.

### GitHub Token Scope

**Error:** `403 Forbidden` when creating a repository.

**Fix:** Your `GITHUB_TOKEN` needs the `repo` scope for creating repositories and pushing files. Regenerate the token at [github.com/settings/tokens](https://github.com/settings/tokens) with the correct scope.

### Source Indexing Timeout

**Error:** `Timeout waiting for source indexing`

The Jules API needs time to discover a newly created repository. This is an eventual-consistency delay.

**Fix:**
- Increase the timeout: `python main.py agent --timeout 3600`
- Or re-run with `status --watch` once indexing completes: `python main.py status <session_id> --watch`

### Gemini API Timeout / Rate Limit

**Error:** `API call timed out` or `429 Too Many Requests`

**What happens automatically:** The CLI retries with exponential backoff. If all retries fail, a comprehensive fallback scaffold is generated so you still get a functional project.

**Manual fix:** Wait a few minutes and try again, or check your Gemini API quota at [Google AI Studio](https://aistudio.google.com/).

### Scraper Returns No Content

**Error:** `Content validation failed: insufficient text length`

The website may be using client-side rendering (JavaScript) or blocking automated requests.

**Fix:** Try a different URL, use **Paste Mode** to provide the content directly, or fall back to **Manual Mode**:
```bash
# Paste the page content from clipboard
python main.py paste --clipboard

# Or provide content inline on the website command
python main.py website --content "The page text..."

# Or describe the idea manually
python main.py manual "My Idea" --description "Inspired by example.com" --watch
```

### Virtual Environment Issues

**Error:** `ModuleNotFoundError: No module named 'src'`

**Fix:** Make sure you're running from the project root _inside_ an activated virtual environment:
```bash
source venv/bin/activate   # Activate
python main.py guide       # Verify
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Setup instructions
- Architecture overview
- Code style requirements (Ruff, mypy)
- Pull request process

All changes must pass the test suite (`python -m pytest tests/ -v`) and type checking (`mypy src/`) before merging.

---

## License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

Copyright © 2026 Jules Jewels AI.
