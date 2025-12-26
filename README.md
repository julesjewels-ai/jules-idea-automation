# Jules Automation Tool

A Python-based CLI tool designed to automate the initial software development lifecycle by generating ideas, creating repositories, and initializing sessions in **Jules**.

## Overview

This tool acts as an "Idea Factory" and Orchestrator. It streamlines the process of starting a new project by:
1.  **Generating Ideas:** Using Google's **Gemini 3** model to generate creative software concepts or extract them from web content.
2.  **Project Factory:** Automatically creating a private **GitHub** repository for the idea.
3.  **Jules Integration:** Instantly creating a **Jules** session linked to the new repository, ready for further development.

## Features

-   **Agent Mode:** Ask Gemini 3 to generate a unique software app idea.
-   **Website Mode:** Scrape a URL and have Gemini 3 extract the core product idea.
-   **Auto-Repo Creation:** Automatically creates a private GitHub repository with a `README.md`.
-   **Jules Session Init:** seamless hand-off to the Jules API.

## Prerequisites

You need the following API keys set in your environment (or a `.env` file):

-   `JULES_API_KEY`: Your API key for the Jules platform.
-   `GEMINI_API_KEY`: API key for Google's Gemini API (Gemini 3 Pro).
-   `GITHUB_TOKEN`: A GitHub Personal Access Token (PAT) with `repo` scope.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-dir>
    ```

2.  **Install Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```env
    JULES_API_KEY=your_jules_key
    GEMINI_API_KEY=your_gemini_key
    GITHUB_TOKEN=your_github_token
    ```

## Usage

The tool is run via the `tool.py` script.

### 1. Generate an Idea (Agent Mode)
Generates a random software idea, creates a GitHub repo, and starts a Jules session.
```bash
python tool.py agent
```

### 2. Extract from Website (Website Mode)
Scrapes the content of a URL, extracts the software idea, creates a GitHub repo, and starts a Jules session.
```bash
python tool.py website --url https://example.com/some-startup-idea
```

### 3. Utility
List available Jules sources (useful for debugging connection).
```bash
python tool.py list-sources
```

## Project Structure

-   `tool.py`: Main entry point and CLI logic.
-   `src/`: Source code.
    -   `gemini_client.py`: Handles interaction with Gemini 3 (generation & structured output).
    -   `github_client.py`: Handles GitHub Repo creation and file management.
    -   `jules_client.py`: Handles Jules Session creation.
    -   `scraper.py`: Web scraping utility.
