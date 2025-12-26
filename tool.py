import argparse
import sys
import json
import os
from dotenv import load_dotenv

load_dotenv()

from src.jules_client import JulesClient
from src.gemini_client import GeminiClient
from src.github_client import GitHubClient
from src.scraper import scrape_text

def process_idea_workflow(idea_data):
    """
    Orchestrates the creation of a GitHub repo and Jules session from an idea.
    idea_data: dict with 'title', 'description', 'slug'
    """
    print(f"Processing Idea: {idea_data['title']}")
    print(f"Slug: {idea_data['slug']}")
    print("-" * 20)

    # 1. GitHub Setup
    gh_client = GitHubClient()
    user = gh_client.get_user()
    username = user['login']
    
    print(f"Creating GitHub repository '{idea_data['slug']}'...")
    gh_client.create_repo(
        name=idea_data['slug'],
        description=idea_data['description'],
        private=True
    )
    
    print("Initializing repository content...")
    readme_content = f"# {idea_data['title']}\n\n{idea_data['description']}"
    gh_client.create_file(
        owner=username,
        repo=idea_data['slug'],
        path="README.md",
        content=readme_content,
        message="Initial commit: Add README with project description"
    )
    
    # 2. Jules Session
    source_id = f"sources/github/{username}/{idea_data['slug']}"
    print(f"Constructed Source ID: {source_id}")
    
    print("Creating session in Jules...")
    jules = JulesClient()
    session = jules.create_session(source_id, idea_data['description'])
    
    print("Session Created!")
    print(json.dumps(session, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Jules Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-sources
    subparsers.add_parser("list-sources", help="List available Jules sources")

    # Command: agent
    agent_parser = subparsers.add_parser("agent", help="Generate an idea using Gemini and send to Jules")
    # No source arg needed, we create it

    # Command: website
    website_parser = subparsers.add_parser("website", help="Scrape a website for an idea and send to Jules")
    website_parser.add_argument("--url", required=True, help="URL to scrape")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "list-sources":
            client = JulesClient()
            sources = client.list_sources()
            print(json.dumps(sources, indent=2))

        elif args.command == "agent":
            print("Generating idea with Gemini...")
            gemini = GeminiClient()
            idea_data = gemini.generate_idea()
            process_idea_workflow(idea_data)

        elif args.command == "website":
            print(f"Scraping {args.url}...")
            text = scrape_text(args.url)
            
            print("Extracting idea with Gemini...")
            gemini = GeminiClient()
            idea_data = gemini.extract_idea_from_text(text)
            process_idea_workflow(idea_data)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
