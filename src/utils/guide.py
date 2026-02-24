"""Interactive guide system for the Jules Automation CLI."""

from src.utils.reporter import Colors, print_panel


def print_welcome_guide() -> None:
    """Display the main welcome guide with all available workflows."""
    
    print("\n")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  Welcome to Jules Idea Automation! 🚀{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print("\n")
    
    intro = f"""This tool automates the end-to-end workflow of turning ideas into 
working prototypes with automated development sessions.

{Colors.BOLD}How it works:{Colors.ENDC}
1. Generate or provide a software idea
2. Create a GitHub repository with MVP scaffold
3. Start an automated Jules development session
4. Watch as your idea becomes a working prototype!"""
    
    print_panel(intro, color=Colors.CYAN, width=70)
    print("\n")
    
    # Three main workflows
    print(f"{Colors.BOLD}{Colors.BLUE}Choose Your Workflow:{Colors.ENDC}\n")
    
    _print_workflow_option(
        number=1,
        emoji="🤖",
        name="Agent Mode",
        command="python main.py agent",
        description="Let Gemini AI generate a creative software idea for you"
    )
    
    _print_workflow_option(
        number=2,
        emoji="🌐",
        name="Website Mode",
        command="python main.py website --url <URL>",
        description="Extract an idea from any public website"
    )
    
    _print_workflow_option(
        number=3,
        emoji="✍️",
        name="Manual Mode",
        command="python main.py manual \"<title>\"",
        description="Provide your own custom idea and details"
    )
    
    print("")
    
    # Quick tips
    tips_content = f"""{Colors.BOLD}Common Options:{Colors.ENDC}
• --watch      Watch the session until completion
• --public     Create a public repository (default: private)
• --category   Target specific type (agent mode only)

{Colors.BOLD}Get Detailed Help:{Colors.ENDC}
• python main.py agent --help
• python main.py website --help
• python main.py manual --help"""
    
    print_panel(tips_content, title="💡 Tips", color=Colors.YELLOW, width=70)
    print("\n")


def _print_workflow_option(number: int, emoji: str, name: str, command: str, description: str) -> None:
    """Print a single workflow option.

    Args:
        number: The option number.
        emoji: The emoji icon for the option.
        name: The name of the option.
        command: The command to execute the option.
        description: A description of the option.
    """
    print(f"  {Colors.BOLD}{number}. {emoji} {name}{Colors.ENDC}")
    print(f"     {Colors.CYAN}{command}{Colors.ENDC}")
    print(f"     {description}")
    print("")


def print_agent_guide() -> None:
    """Display detailed guide for agent mode."""
    
    content = f"""{Colors.BOLD}What is Agent Mode?{Colors.ENDC}
Agent mode uses Google's Gemini AI to generate creative software ideas 
from scratch. Perfect when you want inspiration or a quick prototype.

{Colors.BOLD}Basic Usage:{Colors.ENDC}
python main.py agent

{Colors.BOLD}Target a Specific Category:{Colors.ENDC}
python main.py agent --category cli_tool

{Colors.BOLD}Available Categories:{Colors.ENDC}
• web_app      - Web applications and dashboards
• cli_tool     - Command-line utilities
• api_service  - REST APIs and microservices
• mobile_app   - Mobile applications
• automation   - Automation scripts and tools
• ai_ml        - AI/ML projects and experiments

{Colors.BOLD}Watch Until Complete:{Colors.ENDC}
python main.py agent --watch

{Colors.BOLD}Create Public Repository:{Colors.ENDC}
python main.py agent --public

{Colors.BOLD}What Happens Next?{Colors.ENDC}
1. Gemini generates a unique software idea
2. GitHub repository is created with MVP scaffold
3. Jules session starts with automated development
4. (Optional) Watch progress until PR is created"""
    
    print("")
    print_panel(content, title="🤖 Agent Mode Guide", color=Colors.BLUE, width=70)
    print("")


def print_website_guide() -> None:
    """Display detailed guide for website mode."""
    
    content = f"""{Colors.BOLD}What is Website Mode?{Colors.ENDC}
Website mode extracts software ideas from public web pages. Perfect 
when you found an interesting concept online and want to build it.

{Colors.BOLD}Basic Usage:{Colors.ENDC}
python main.py website --url https://example.com

{Colors.BOLD}With Watch Mode:{Colors.ENDC}
python main.py website --url https://example.com --watch

{Colors.BOLD}Create Public Repository:{Colors.ENDC}
python main.py website --url https://example.com --public

{Colors.BOLD}Requirements:{Colors.ENDC}
• URL must be publicly accessible (no login required)
• Page should contain clear description of the software idea
• Works best with blog posts, project pages, documentation

{Colors.BOLD}What Happens Next?{Colors.ENDC}
1. Website content is scraped and analyzed
2. Gemini extracts the core software idea
3. GitHub repository is created with MVP scaffold
4. Jules session starts with automated development
5. (Optional) Watch progress until PR is created

{Colors.BOLD}Troubleshooting:{Colors.ENDC}
If scraping fails:
• Ensure URL is publicly accessible
• Try a different URL with clearer content
• Use 'agent' mode as an alternative"""
    
    print("")
    print_panel(content, title="🌐 Website Mode Guide", color=Colors.CYAN, width=70)
    print("")


def print_manual_guide() -> None:
    """Display detailed guide for manual mode."""
    
    content = f"""{Colors.BOLD}What is Manual Mode?{Colors.ENDC}
Manual mode lets you provide your own software idea details. Perfect 
when you know exactly what you want to build.

{Colors.BOLD}Basic Usage (Title Only):{Colors.ENDC}
python main.py manual \"My Awesome Tool\"

{Colors.BOLD}Full Options:{Colors.ENDC}
python main.py manual \"Task Manager\" \\
  --description \"A CLI tool for managing daily tasks\" \\
  --slug my-task-cli \\
  --tech_stack \"Python,Click,SQLite\" \\
  --features \"CRUD operations,Priority tags,Export CSV\" \\
  --watch

{Colors.BOLD}Required Inputs:{Colors.ENDC}
• title         Project name (positional argument)

{Colors.BOLD}Optional Inputs:{Colors.ENDC}
• --description  Detailed project description (defaults to title)
• --slug         Custom repository name (auto-generated if omitted)
• --tech_stack   Comma-separated list of technologies
• --features     Comma-separated list of key features
• --public       Create public repository (default: private)
• --watch        Watch session until completion

{Colors.BOLD}Tips:{Colors.ENDC}
• Slugs are auto-generated in kebab-case from title
• Very long titles (>100 chars) are handled gracefully
• Tech stack and features help guide the scaffolding
• If title is very long, it's used as description

{Colors.BOLD}What Happens Next?{Colors.ENDC}
1. Your idea details are validated
2. GitHub repository is created with MVP scaffold
3. Jules session starts with automated development
4. (Optional) Watch progress until PR is created"""
    
    print("")
    print_panel(content, title="✍️  Manual Mode Guide", color=Colors.GREEN, width=70)
    print("")


def print_examples() -> None:
    """Display common usage examples."""
    
    content = f"""{Colors.BOLD}Quick Start - Generate Random Idea:{Colors.ENDC}
python main.py agent

{Colors.BOLD}Generate CLI Tool with Auto-Watch:{Colors.ENDC}
python main.py agent --category cli_tool --watch

{Colors.BOLD}Extract Idea from Website:{Colors.ENDC}
python main.py website --url https://news.ycombinator.com/item?id=12345

{Colors.BOLD}Manual Entry - Minimal:{Colors.ENDC}
python main.py manual \"Budget Tracker\"

{Colors.BOLD}Manual Entry - Detailed:{Colors.ENDC}
python main.py manual \"Smart Home Dashboard\" \\
  --description \"Real-time IoT device monitoring and control\" \\
  --tech_stack \"React,Node.js,WebSockets,PostgreSQL\" \\
  --features \"Device monitoring,Alert system,Usage analytics\" \\
  --public --watch

{Colors.BOLD}Check Session Status:{Colors.ENDC}
python main.py status <session_id>

{Colors.BOLD}Watch Existing Session:{Colors.ENDC}
python main.py status <session_id> --watch

{Colors.BOLD}List Available Sources:{Colors.ENDC}
python main.py list-sources"""
    
    print("")
    print_panel(content, title="📚 Usage Examples", color=Colors.HEADER, width=70)
    print("")
