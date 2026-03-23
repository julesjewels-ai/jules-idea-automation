# Development Log

## Project: Jules Automation Tool

This log documents the development journey, design decisions, and evolution of the Jules Automation Tool.

### Phase 10: Checklist Template Clarity & Project-Aware Production Items

**Date:** 2026-03-23

**Changes:**

Improved the static fallback checklists generated in new repositories when AI-powered feature map generation is unavailable.

1. **Template Notice Banner:**
   - Both MVP and Production checklists now display a `⚠️ TEMPLATE` callout when using static fallback items, making it clear these are generic starting points — not custom-generated.
   - AI-generated checklists remain unchanged (no banner).

2. **Project-Aware Production Checklist:**
   - `_static_production_items()` now accepts the `idea` dictionary and uses `tech_stack` to conditionally include:
     - **API items** (Health check, Rate limiting, API docs) only when tech stack includes frameworks like FastAPI, Flask, Django, Express, etc.
     - **Database items** (Database migrations) only when tech stack includes PostgreSQL, MySQL, MongoDB, Redis, etc.
   - Non-applicable items are no longer included, reducing noise for CLI-only or non-DB projects.

**Files Changed:**
- `src/templates/feature_map.py` — Added `_TEMPLATE_NOTICE`, made `_static_production_items()` project-aware
- `tests/templates/test_feature_map.py` — 8 new tests: template notice presence/absence, API/DB conditional items, non-API/non-DB stacks

**Rationale:**
Users were confused by static fallback checklists that appeared custom-generated. The template banner clarifies provenance, and conditional items reduce irrelevant noise.

---

### Phase 9: Paste-Content Input Modes

**Date:** 2026-03-18

**Changes:**

Added a fourth input mode (`paste`) and a `--content` flag on `website` to allow direct content input for idea extraction, bypassing the web scraper entirely.

1. **New `paste` Command:**
   - `--clipboard` — Auto-read from macOS clipboard via `pbpaste` (recommended)
   - `--file <path>` — Read content from a text file
   - `-` (stdin) — Pipe content from another command
   - Interactive mode — Paste content, then type `END` to submit

2. **`website --content` Flag:**
   - `--url` and `--content` are now mutually exclusive
   - `--content` skips the scraper and feeds text directly to `gemini.extract_idea_from_text()`

3. **UX Improvements:**
   - Content preview shown before Gemini processing (source label, char count, first 200 chars)
   - Minimum 200-char content validation

**Files Changed:**
- `src/cli/parser.py` — New `paste` subcommand, `--content` on `website`
- `src/cli/commands.py` — `handle_paste()`, `_read_clipboard()`, `_read_paste_content()`, content preview in `handle_paste()`
- `tests/cli/test_commands_paste.py` — 13 tests covering all input modes
- `README.md` — Updated Key Features, Mermaid diagram, Paste Mode section, CLI Reference, Available Commands, Troubleshooting

**Rationale:**
Users frequently encounter corporate firewalls, JS-rendered pages, or anti-scraping protections. Paste mode provides a zero-dependency fallback: copy the text, run `jules paste --clipboard`, done.

---

### Phase 8: In-CLI User Guide System

**Date:** 2026-01-11

**Changes:**

Implemented comprehensive in-CLI user guide system to improve discoverability and user onboarding:

1. **New Commands:**
   - `guide` - Interactive user guide showing all workflows
     - Supports `--workflow` flag for targeted help (agent/website/manual)
   - `manual` - Provide custom idea details (completes the three-workflow vision)
     - Auto-generates kebab-case slug from title
     - Handles long titles gracefully (Description-as-Title pattern)
     - Supports description, slug, tech_stack, features arguments

2. **New Utilities:**
   - `src/utils/slugify.py` - GitHub-compliant slug generation (100-char limit)
   - `src/utils/guide.py` - Interactive guide system with formatted panels
     - Welcome guide, per-workflow guides, usage examples

3. **Enhanced Files:**
   - `src/cli/parser.py` - Added guide and manual parsers
   - `src/cli/commands.py` - Added `handle_guide()` and `handle_manual()`
   - `main.py` - Guide tip when no command provided
   - `README.md` - Reorganized with three main workflows prominently featured

**Rationale:**
The CLI had powerful functionality but lacked discoverability. The guide system provides interactive, context-aware help following established CLI UX standards while maintaining SOLID principles.

---

### Phase 1: Inception & Core Requirements

**Goal:** Create an automation tool to feed software ideas into the Jules API.

**Initial Plan:**
-   Build a Python CLI.
-   Integrate with **Jules API** to create sessions.
-   Integrate with **Gemini 3** (via `google-genai` SDK) to generate ideas.
-   Implement a web scraper to source ideas from URLs.

**Key Decisions:**
-   **Tech Stack:** Python was chosen for its strong support for API interaction and scraping (`requests`, `beautifulsoup4`).
-   **AI Model:** Explicitly selected `gemini-3-pro-preview` per user requirements to leverage the latest reasoning capabilities.
-   **Source Identification:** Initially, the plan was to ask the user for an existing Jules Source ID (GitHub repo) to attach the session to.

### Phase 2: The "Project Factory" Evolution

**Requirement Update:**
The user requested an enhancement to the workflow: **Automated Repository Creation**. Instead of using an existing source, the tool should act as a "Project Factory."

**Workflow Shift:**
1.  **Old Workflow:** Generate Idea -> Ask User for Source -> Create Session.
2.  **New Workflow:** Generate Idea -> **Create New GitHub Repo** -> **Initialize Content** -> Construct Source ID -> Create Session.

**Technical Implementation:**
-   **GitHub Integration:** Added `src/github_client.py` using the GitHub REST API.
    -   Implemented `create_repo` to generate private repositories.
    -   Implemented `create_file` to bootstrap the `README.md` immediately, ensuring the repo is not empty and has a `main` branch.
-   **Structured AI Output:**
    -   Modified `GeminiClient` to return structured JSON (`title`, `description`, `slug`).
    -   The `slug` is crucial for creating valid, clean GitHub repository names (e.g., `my-awesome-app`).
    -   Used `pydantic` models to define the expected schema for Gemini.

### Challenges & Solutions

-   **Dependencies:** Switched to the new `google-genai` SDK to access Gemini 3 features. ensuring `pydantic` compatibility.
-   **Environment Variables:** Adopted `python-dotenv` early to manage the growing list of keys (`JULES`, `GEMINI`, `GITHUB`).
-   **Repo Initialization:** GitHub repos created via API are empty by default. To make them usable by Jules immediately, we added a step to commit a `README.md` via the API, which implicitly creates the default branch.

---

### Phase 3: Category Targeting & Open Source by Default

**Date:** 2025-12-26

**New Features:**

1.  **Category-Aware Idea Generation:**
    -   Added `--category` flag to target specific project types: `web_app`, `cli_tool`, `api_service`, `mobile_app`, `automation`, `ai_ml`.
    -   Each category has a tailored prompt to generate more relevant ideas.

2.  **Enhanced Idea Output:**
    -   Ideas now include `tech_stack[]` and `features[]` arrays.
    -   README.md is automatically enriched with these sections.

3.  **Public Repositories by Default:**
    -   Repos are now created as **public** by default (open source!).
    -   Use `--private` flag to create private repositories.
    -   Verified `.env` is in `.gitignore` to prevent secret exposure.

4.  **Configurable Timeout:**
    -   Added `--timeout` flag (default: 1800s = 30 minutes).
    -   Controls how long to wait for Jules to index new repositories.

5.  **Simple Reporting:**
    -   Added `print_report()` function that summarizes the workflow.
    -   Shows project name, repo URL, and Jules session URL.

**Files Changed:**
-   `src/gemini_client.py` - Category prompts, enhanced `IdeaResponse` model
-   `tool.py` - New CLI args, updated workflow, reporting
-   `.env.example` - Documentation for required environment variables
-   `docs/ROADMAP.md` - Future phases documented

---

### Phase 4: Enhanced Session Tracking

**Date:** 2025-12-26

**New Features:**

1.  **Session Tracking API Methods:**
    -   `get_session(session_id)` - Retrieve session details
    -   `list_sessions(page_size)` - List recent sessions
    -   `list_activities(session_id)` - Get progress updates
    -   `send_message(session_id, prompt)` - Send follow-up messages
    -   `approve_plan(session_id)` - Approve pending plans
    -   `is_session_complete(session_id)` - Check completion status and PR URL

2.  **Watch Mode:**
    -   Added `--watch` flag to `agent` and `website` commands
    -   Polls session every 30 seconds until completion
    -   Displays live progress updates and final PR URL

3.  **Status Command:**
    -   New `status <session_id>` command
    -   Shows session title, URL, completion status, and recent activity
    -   Supports `--watch` flag for continuous monitoring

**Files Changed:**
-   `src/jules_client.py` - 6 new session tracking methods
-   `tool.py` - `--watch` flags, `status` command, `watch_session()` function

---

### Phase 5: MVP Scaffolding with SOLID Principles

**Date:** 2025-12-27

**New Features:**

1.  **AI-Generated Project Structure:**
    -   Uses Gemini to generate complete MVP scaffold based on the idea
    -   Creates modular `src/` directory structure (core/, services/, utils/)
    -   Follows SOLID principles with clean separation of concerns
    -   Main script is orchestration-only, no business logic

2.  **Pydantic Models for Scaffold:**
    -   `ProjectFile` - Represents a single file with path, content, description
    -   `ProjectScaffold` - Contains files[], requirements[], run_command

3.  **Batch File Creation:**
    -   New `GitHubClient.create_files()` method using Git Data API
    -   Creates all scaffold files in a single commit
    -   Much more efficient than individual file creation

4.  **Enhanced README:**
    -   Automatically includes Setup and Usage sections
    -   Shows pip install command from requirements
    -   Documents run command from scaffold

**Files Changed:**
-   `src/gemini_client.py` - `ProjectFile`, `ProjectScaffold` models, `generate_project_scaffold()`
-   `src/github_client.py` - `create_files()` for batch commits
-   `tool.py` - Integration of scaffold generation into workflow

---

### Phase 6: SOLID Refactoring

**Date:** 2025-12-27

**Changes:**

Refactored monolithic `tool.py` (387 lines) into clean modular structure:

```
main.py              # Entry point (orchestration only)
src/
├── cli/             # Argument parsing, command handlers
├── core/            # Workflow, models, README builder
├── services/        # Gemini, GitHub, Jules, Scraper
└── utils/           # Polling, reporter
```

**Key Improvements:**
-   **SRP**: Each file has one responsibility
-   **DIP**: `IdeaWorkflow` uses dependency injection
-   **Testability**: Services can be mocked for unit tests

**Usage:** `python3 main.py agent --category cli_tool`

---

### Phase 7: Developer-Ready MVP Scaffolds

**Date:** 2025-12-27

**Changes:**

Enhanced the generated MVP scaffolds to be immediately runnable by developers:

1.  **Expanded Scaffold Files:**
    -   `main.py` - Now includes argparse CLI with `--help` and `--version`
    -   `src/core/app.py` - Business logic with clear docstrings
    -   `Makefile` - `install`, `run`, `test`, `clean` targets
    -   `.env.example` - Environment variable template
    -   `tests/test_core.py` - Runnable unit tests with pytest
    -   Total: 9 files (up from 5)

2.  **Enhanced README Template:**
    -   Added **Quick Start** section with one-liner setup
    -   Added **Development** section with Makefile commands
    -   Added **Testing** section with pytest command

3.  **Improved Fallback Scaffold:**
    -   Now generates full developer-ready structure even on API failure

**Files Changed:**
-   `src/services/gemini.py` - Enhanced prompt and fallback scaffold
-   `src/core/readme_builder.py` - Added developer-focused sections

---

### Future Improvements
-   Add error handling for repo name collisions
-   Support for configuring the GitHub organization
-   Add unit tests with mocked services

