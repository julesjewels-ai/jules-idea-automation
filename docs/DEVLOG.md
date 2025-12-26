# Development Log

## Project: Jules Automation Tool

This log documents the development journey, design decisions, and evolution of the Jules Automation Tool.

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

### Future Improvements
-   Add error handling for repo name collisions (currently, GitHub API will return 422 if the repo exists).
-   Support for configuring the GitHub organization (currently defaults to the authenticated user).
-   Add support for `auto_init` with specific `.gitignore` templates.
