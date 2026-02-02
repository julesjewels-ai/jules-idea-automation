# Jules Automation Tool

A Python CLI tool that automates the software development lifecycle by generating ideas, creating repositories, and initializing Jules sessions.

## Overview

This tool acts as an "Idea Factory" that:
1. **Generates Ideas:** Uses Google's Gemini 3 to generate or extract software concepts
2. **Creates Repos:** Automatically creates a GitHub repository with MVP scaffold
3. **Starts Jules:** Creates a Jules session linked to the new repository

## Prerequisites

Set these API keys in a `.env` file:
- `JULES_API_KEY` - Jules platform API key
- `GEMINI_API_KEY` - Google Gemini API key
- `GITHUB_TOKEN` - GitHub PAT with `repo` scope

## Installation

```bash
git clone <your-repo-url>
cd jules-idea-automation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:
```env
JULES_API_KEY=your_jules_key
GEMINI_API_KEY=your_gemini_key
GITHUB_TOKEN=your_github_token
```

## Usage

### Getting Started

If you're new to the tool, start with the interactive guide:

```bash
python main.py guide
```

### Three Main Workflows

**🤖 Agent Mode** - Let Gemini AI generate ideas:

```bash
# Generate a random idea
python main.py agent

# Generate a targeted idea (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)
python main.py agent --category cli_tool

# Watch session until PR is created
python main.py agent --watch
```

**🌐 Website Mode** - Extract ideas from websites:

```bash
# Extract idea from a website
python main.py website --url https://example.com

# Watch session until completion
python main.py website --url https://example.com --watch
```

**✍️ Manual Mode** - Provide your own custom idea:

```bash
# Basic (title only)
python main.py manual "My Awesome Tool"

# Full options
python main.py manual "Task Manager" \
  --description "A CLI tool for managing daily tasks" \
  --slug my-task-cli \
  --tech_stack "Python,Click,SQLite" \
  --features "CRUD operations,Priority tags,Export CSV" \
  --watch
```

### Other Commands

```bash
# Check session status
python main.py status <session_id>

# List available sources
python main.py list-sources

# Get detailed help for a specific workflow
python main.py guide --workflow agent
```

### Options

| Flag | Description |
|------|-------------|
| `--category` | Target a specific idea category |
| `--private` | Create private repo (default: public) |
| `--timeout` | Timeout in seconds (default: 1800) |
| `--watch` | Watch session until completion |

## Project Structure

```
main.py              # Entry point (orchestration only)
docs/                # Project documentation & contracts
├── PRD.md, ARCHITECTURE.md, GUARDRAILS.md...
src/
├── cli/             # Argument parsing, command handlers
├── core/            # Workflow, models, README builder
├── services/        # Gemini, GitHub, Jules, Scraper
└── utils/           # Polling, reporter
agent/               # Agent configuration & automation
├── config/          # Agent configs (architect, coder, etc.)
├── prompts/         # Agent system prompts
├── scripts/         # Automation scripts
├── progress/        # Agent progress tracking
└── reports/         # Agent completion reports
```
