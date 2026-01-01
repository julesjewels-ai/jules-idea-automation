# Jules Automation Tool

[![Website](https://img.shields.io/badge/Website-Visit%20Site-blue)](https://julesjewels-ai.github.io/jules-idea-automation/)

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

Run via `main.py`:

```bash
# Generate a random idea
python main.py agent

# Generate a targeted idea (web_app, cli_tool, api_service, mobile_app, automation, ai_ml)
python main.py agent --category cli_tool

# Extract idea from a website
python main.py website --url https://example.com

# Watch session until PR is created
python main.py agent --watch

# Check session status
python main.py status <session_id>

# List available sources
python main.py list-sources
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
src/
├── cli/             # Argument parsing, command handlers
├── core/            # Workflow, models, README builder
├── services/        # Gemini, GitHub, Jules, Scraper
└── utils/           # Polling, reporter
```
