# Jules Automation Tool

[![Website](https://img.shields.io/badge/Website-Visit%20Site-blue)](https://julesjewels-ai.github.io/jules-idea-automation/)

A Python CLI tool that automates the software development lifecycle by generating ideas, creating repositories, and initializing Jules sessions.

## Overview

This tool acts as an "Idea Factory" that:
1. **Generates Ideas:** Uses Google's Gemini 3 (Thinking Mode) to generate or extract software concepts.
2. **Creates Repos:** Automatically creates a GitHub repository with a SOLID MVP scaffold.
3. **Starts Jules:** Creates a Jules session linked to the new repository for autonomous development.
4. **Web UI:** Provides a beautiful landing page for project overview and quick setup.

## 🌐 Web Interface

The project includes a modern, responsive web interface located in the `website/` directory.

- **Landing Page:** Interactive overview of features and workflow.
- **Terminal Demo:** Visual representation of the CLI in action.
- **Mobile Optimized:** Fully responsive design with glassmorphism aesthetics.

To view the site locally:
```bash
open website/index.html
```

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

The tool provides several commands to manage your developer lifecycle:

### 🤖 Agent Mode
Generate a new idea from scratch.
```bash
# Generate a random idea
python main.py agent

# Generate a targeted idea by category
# Categories: web_app, cli_tool, api_service, mobile_app, automation, ai_ml
python main.py agent --category cli_tool --watch
```

### 🌐 Website Mode
Extract an idea from an existing URL.
```bash
# Point to a blog post, GitHub issue, or landing page
python main.py website --url https://example.com/idea --watch
```

### 📊 Status & Tracking
Monitor active sessions.
```bash
# Check progress and get PR URL
python main.py status <session_id>

# Watch until completion
python main.py status <session_id> --watch

# List your Jules sources
python main.py list-sources
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--category` | Target a specific idea category | None |
| `--private` | Create private repo (instead of public) | False |
| `--timeout` | Timeout in seconds for indexing/watching | 1800 |
| `--watch` | Live-poll session until completion | False |
| `--url` | Target URL for website mode | Required |

## 🛡️ Security

Security is a first-class citizen in the Jules Automation Tool:

1. **SSRF Protection:** Web scraping includes hostname resolution and private IP blocking to prevent Server-Side Request Forgery.
2. **Content Validation:** Ingested text is validated for meaningful content and blocked-access indicators.
3. **Network Robustness:** All external API calls (GitHub, Jules) include a 30-second timeout to prevent application hangs.
4. **Credential Safety:** Automated `.gitignore` patterns prevent accidental exposure of `.env` files.

## Project Structure

```
main.py              # Entry point (orchestration only)
src/
├── cli/             # Argument parsing, command handlers
├── core/            # Workflow, models, README builder
├── services/        # Gemini, GitHub, Jules, Scraper
└── utils/           # Polling, reporter
```
