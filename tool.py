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

def process_idea_workflow(idea_data, private=False, timeout=1800):
    """
    Orchestrates the creation of a GitHub repo and Jules session from an idea.
    
    Args:
        idea_data: dict with 'title', 'description', 'slug', 'tech_stack', 'features'
        private: If True, create a private repository. Default is public.
        timeout: Max seconds to wait for Jules indexing (default: 1800 = 30 min)
    """
    print(f"Processing Idea: {idea_data['title']}")
    print(f"Slug: {idea_data['slug']}")
    print("-" * 40)

    # 1. GitHub Setup
    gh_client = GitHubClient()
    user = gh_client.get_user()
    username = user['login']
    
    visibility = "private" if private else "public"
    print(f"Creating {visibility} GitHub repository '{idea_data['slug']}'...")
    gh_client.create_repo(
        name=idea_data['slug'],
        description=idea_data['description'][:350],
        private=private
    )
    
    # Generate MVP scaffold with Gemini
    print("Generating MVP scaffold with Gemini (this may take a moment)...")
    gemini = GeminiClient()
    scaffold = gemini.generate_project_scaffold(idea_data)
    
    # Build enhanced README with tech stack, features, and run instructions
    readme_lines = [
        f"# {idea_data['title']}",
        "",
        idea_data['description'],
        "",
    ]
    
    if idea_data.get('tech_stack'):
        readme_lines.extend([
            "## Tech Stack",
            "",
            *[f"- {tech}" for tech in idea_data['tech_stack']],
            "",
        ])
    
    if idea_data.get('features'):
        readme_lines.extend([
            "## Features",
            "",
            *[f"- {feature}" for feature in idea_data['features']],
            "",
        ])
    
    # Add setup and run instructions from scaffold
    if scaffold.get('requirements'):
        readme_lines.extend([
            "## Setup",
            "",
            "```bash",
            "pip install -r requirements.txt",
            "```",
            "",
        ])
    
    if scaffold.get('run_command'):
        readme_lines.extend([
            "## Usage",
            "",
            "```bash",
            scaffold['run_command'],
            "```",
            "",
        ])
    
    readme_content = "\n".join(readme_lines)
    
    # First commit: Create README to initialize the repo
    print("Initializing repository with README...")
    gh_client.create_file(
        owner=username,
        repo=idea_data['slug'],
        path="README.md",
        content=readme_content,
        message="Initial commit: Add README with project description"
    )
    
    # Second commit: Add all scaffold files
    if scaffold.get('files'):
        print(f"Adding {len(scaffold['files'])} MVP files...")
        
        # Prepare files for batch creation
        files_to_create = []
        for file_info in scaffold['files']:
            # Skip README.md since we already created it
            if file_info['path'].lower() == 'readme.md':
                continue
            files_to_create.append({
                'path': file_info['path'],
                'content': file_info['content']
            })
        
        # Add requirements.txt if we have dependencies
        if scaffold.get('requirements'):
            files_to_create.append({
                'path': 'requirements.txt',
                'content': '\n'.join(scaffold['requirements'])
            })
        
        if files_to_create:
            result = gh_client.create_files(
                owner=username,
                repo=idea_data['slug'],
                files=files_to_create,
                message="feat: Add MVP scaffold with SOLID structure"
            )
            print(f"  Created {result['files_created']} files in single commit")
    
    repo_url = f"https://github.com/{username}/{idea_data['slug']}"
    
    # 2. Jules Session
    source_id = f"sources/github/{username}/{idea_data['slug']}"
    print(f"Constructed Source ID: {source_id}")
    
    import time
    jules = JulesClient()
    
    # Poll for the source to be indexed by Jules
    print(f"Waiting for Jules to discover the new repository (timeout: {timeout}s)...")
    poll_interval = 10  # Check every 10 seconds
    elapsed = 0
    source_found = False
    
    while elapsed < timeout:
        if jules.source_exists(source_id):
            source_found = True
            print(f"Source found after {elapsed}s!")
            break
        print(f"  Source not yet indexed ({elapsed}s elapsed, checking again in {poll_interval}s)...")
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    if not source_found:
        print(f"WARNING: Source '{source_id}' was not found in Jules after {timeout}s.")
        print("This may be because the Jules GitHub app is not installed on this repository.")
        print("Please visit https://jules.google.com to install the app and try again.")
        # Still print partial report
        print_report(idea_data, repo_url, None)
        return None
    
    print("Creating session in Jules...")
    session = jules.create_session(source_id, idea_data['description'])
    
    # Print simple report
    print_report(idea_data, repo_url, session)
    
    return session


def print_report(idea_data, repo_url, session, pr_url=None):
    """Prints a simple summary report of the workflow results."""
    print("")
    print("=" * 50)
    print("✨ WORKFLOW COMPLETE")
    print("=" * 50)
    print(f"📦 Project: {idea_data['title']}")
    print(f"📝 Slug:    {idea_data['slug']}")
    print(f"🔗 Repo:    {repo_url}")
    if session:
        print(f"🤖 Jules:   {session.get('url', 'N/A')}")
        print(f"   Session: {session.get('id', 'N/A')}")
        if pr_url:
            print(f"🎉 PR:      {pr_url}")
    else:
        print("⚠️  Jules session was not created (source not indexed)")
    print("=" * 50)


def watch_session(session_id, timeout=1800):
    """Watches a Jules session until completion or timeout.
    
    Args:
        session_id: The session ID to watch
        timeout: Max seconds to wait (default: 30 min)
    
    Returns:
        tuple: (is_complete, pr_url or None)
    """
    import time
    
    jules = JulesClient()
    poll_interval = 30  # Check every 30 seconds
    elapsed = 0
    
    print(f"\n👀 Watching session {session_id} (timeout: {timeout}s)...")
    
    while elapsed < timeout:
        is_complete, pr_url = jules.is_session_complete(session_id)
        
        if is_complete:
            print(f"\n✅ Session completed after {elapsed}s!")
            if pr_url:
                print(f"🎉 Pull Request: {pr_url}")
            else:
                print("ℹ️  Session completed but no PR was created.")
            return is_complete, pr_url
        
        # Show latest activity
        try:
            activities = jules.list_activities(session_id, page_size=1)
            if activities.get("activities"):
                latest = activities["activities"][0]
                title = latest.get("progressUpdated", {}).get("title", "Working...")
                print(f"  [{elapsed}s] {title[:60]}...")
        except Exception:
            print(f"  [{elapsed}s] Polling...")
        
        time.sleep(poll_interval)
        elapsed += poll_interval
    
    print(f"\n⏱️  Timeout reached after {timeout}s. Session still running.")
    session = jules.get_session(session_id)
    print(f"   Check status at: {session.get('url', 'N/A')}")
    return False, None


def main():
    parser = argparse.ArgumentParser(description="Jules Automation Tool")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: list-sources
    subparsers.add_parser("list-sources", help="List available Jules sources")

    # Command: agent
    agent_parser = subparsers.add_parser("agent", help="Generate an idea using Gemini and send to Jules")
    agent_parser.add_argument(
        "--category", 
        choices=["web_app", "cli_tool", "api_service", "mobile_app", "automation", "ai_ml"],
        help="Target a specific category for idea generation"
    )
    agent_parser.add_argument(
        "--private",
        action="store_true",
        help="Create a private repository (default: public)"
    )
    agent_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,  # 30 minutes in seconds
        help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    agent_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session until completion and show PR URL"
    )

    # Command: website
    website_parser = subparsers.add_parser("website", help="Scrape a website for an idea and send to Jules")
    website_parser.add_argument("--url", required=True, help="URL to scrape")
    website_parser.add_argument(
        "--private",
        action="store_true",
        help="Create a private repository (default: public)"
    )
    website_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for Jules indexing (default: 1800 = 30 min)"
    )
    website_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session until completion and show PR URL"
    )

    # Command: status
    status_parser = subparsers.add_parser("status", help="Check status of a Jules session")
    status_parser.add_argument("session_id", help="The session ID to check")
    status_parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch the session until completion"
    )
    status_parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Timeout in seconds for watching (default: 1800 = 30 min)"
    )

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
            category = getattr(args, 'category', None)
            print(f"Generating idea with Gemini{f' (category: {category})' if category else ''}...")
            gemini = GeminiClient()
            idea_data = gemini.generate_idea(category=category)
            session = process_idea_workflow(
                idea_data, 
                private=args.private, 
                timeout=args.timeout
            )
            
            # Watch mode: poll for completion
            if session and args.watch:
                watch_session(session.get('id'), timeout=args.timeout)

        elif args.command == "website":
            print(f"Scraping {args.url}...")
            text = scrape_text(args.url)
            
            print("Extracting idea with Gemini...")
            gemini = GeminiClient()
            idea_data = gemini.extract_idea_from_text(text)
            session = process_idea_workflow(
                idea_data, 
                private=args.private, 
                timeout=args.timeout
            )
            
            # Watch mode: poll for completion
            if session and args.watch:
                watch_session(session.get('id'), timeout=args.timeout)

        elif args.command == "status":
            client = JulesClient()
            session_id = args.session_id
            
            if args.watch:
                watch_session(session_id, timeout=args.timeout)
            else:
                # Just show current status
                session = client.get_session(session_id)
                is_complete, pr_url = client.is_session_complete(session_id)
                
                print(f"\n📋 Session Status: {session_id}")
                print(f"   Title:    {session.get('title', 'N/A')}")
                print(f"   URL:      {session.get('url', 'N/A')}")
                print(f"   Complete: {'✅ Yes' if is_complete else '⏳ In Progress'}")
                if pr_url:
                    print(f"   PR:       {pr_url}")
                
                # Show latest activity
                activities = client.list_activities(session_id, page_size=3)
                if activities.get("activities"):
                    print("\n   Recent Activity:")
                    for act in activities["activities"][:3]:
                        progress = act.get("progressUpdated", {})
                        title = progress.get("title", "")
                        if title:
                            print(f"   - {title[:70]}")

    except Exception as e:
        if hasattr(e, 'response') and e.response is not None:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
