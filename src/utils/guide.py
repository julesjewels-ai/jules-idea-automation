"""Interactive guide system for the Jules Automation CLI."""

from src.utils.reporter import Colors, print_panel


def print_welcome_guide() -> None:
    """Display the main welcome guide with all available workflows."""

    print("\n")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}  Welcome to Jules Idea Automation! 🚀{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print("\n")

    intro = (f"This tool automates the end-to-end workflow of turning ideas into\n"
             f"working prototypes with automated development sessions.\n\n"
             f"{Colors.BOLD}How it works:{Colors.ENDC}\n"
             "1. Generate or provide a software idea\n"
             "2. Create a GitHub repository with MVP scaffold\n"
             "3. Start an automated Jules development session\n"
             "4. Watch as your idea becomes a working prototype!")

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
    tips_content = (f"{Colors.BOLD}Common Options:{Colors.ENDC}\n"
                    "• --watch      Watch the session until completion\n"
                    "• --private    Create a private repository (default: public)\n"
                    "• --category   Target specific type (agent mode only)\n\n"
                    f"{Colors.BOLD}Get Detailed Help:{Colors.ENDC}\n"
                    "• python main.py agent --help\n"
                    "• python main.py website --help\n"
                    "• python main.py manual --help")

    print_panel(tips_content, title="💡 Tips", color=Colors.YELLOW, width=70)
    print("\n")


def _print_workflow_option(
        number: int,
        emoji: str,
        name: str,
        command: str,
        description: str) -> None:
    """Print a single workflow option."""
    print(f"  {Colors.BOLD}{number}. {emoji} {name}{Colors.ENDC}")
    print(f"     {Colors.CYAN}{command}{Colors.ENDC}")
    print(f"     {description}")
    print("")


def print_agent_guide() -> None:
    """Display detailed guide for agent mode."""

    content = (f"{Colors.BOLD}What is Agent Mode?{Colors.ENDC}\n"
               "Agent mode uses Google's Gemini AI to generate creative software ideas\n"
               "from scratch. Perfect when you want inspiration or a quick prototype.\n\n"
               f"{Colors.BOLD}Basic Usage:{Colors.ENDC}\n"
               "python main.py agent\n\n"
               f"{Colors.BOLD}Target a Specific Category:{Colors.ENDC}\n"
               "python main.py agent --category cli_tool\n\n"
               f"{Colors.BOLD}Available Categories:{Colors.ENDC}\n"
               "• web_app      - Web applications and dashboards\n"
               "• cli_tool     - Command-line utilities\n"
               "• api_service  - REST APIs and microservices\n"
               "• mobile_app   - Mobile applications\n"
               "• automation   - Automation scripts and tools\n"
               "• ai_ml        - AI/ML projects and experiments\n\n"
               f"{Colors.BOLD}Watch Until Complete:{Colors.ENDC}\n"
               "python main.py agent --watch\n\n"
               f"{Colors.BOLD}Create Private Repository:{Colors.ENDC}\n"
               "python main.py agent --private\n\n"
               f"{Colors.BOLD}What Happens Next?{Colors.ENDC}\n"
               "1. Gemini generates a unique software idea\n"
               "2. GitHub repository is created with MVP scaffold\n"
               "3. Jules session starts with automated development\n"
               "4. (Optional) Watch progress until PR is created")

    print("")
    print_panel(
        content,
        title="🤖 Agent Mode Guide",
        color=Colors.BLUE,
        width=70)
    print("")


def print_website_guide() -> None:
    """Display detailed guide for website mode."""

    content = (f"{Colors.BOLD}What is Website Mode?{Colors.ENDC}\n"
               "Website mode extracts software ideas from public web pages. Perfect\n"
               "when you found an interesting concept online and want to build it.\n\n"
               f"{Colors.BOLD}Basic Usage:{Colors.ENDC}\n"
               "python main.py website --url https://example.com\n\n"
               f"{Colors.BOLD}With Watch Mode:{Colors.ENDC}\n"
               "python main.py website --url https://example.com --watch\n\n"
               f"{Colors.BOLD}Create Private Repository:{Colors.ENDC}\n"
               "python main.py website --url https://example.com --private\n\n"
               f"{Colors.BOLD}Requirements:{Colors.ENDC}\n"
               "• URL must be publicly accessible (no login required)\n"
               "• Page should contain clear description of the software idea\n"
               "• Works best with blog posts, project pages, documentation\n\n"
               f"{Colors.BOLD}What Happens Next?{Colors.ENDC}\n"
               "1. Website content is scraped and analyzed\n"
               "2. Gemini extracts the core software idea\n"
               "3. GitHub repository is created with MVP scaffold\n"
               "4. Jules session starts with automated development\n"
               "5. (Optional) Watch progress until PR is created\n\n"
               f"{Colors.BOLD}Troubleshooting:{Colors.ENDC}\n"
               "If scraping fails:\n"
               "• Ensure URL is publicly accessible\n"
               "• Try a different URL with clearer content\n"
               "• Use 'agent' mode as an alternative")

    print("")
    print_panel(
        content,
        title="🌐 Website Mode Guide",
        color=Colors.CYAN,
        width=70)
    print("")


def print_manual_guide() -> None:
    """Display detailed guide for manual mode."""

    content = (f"{Colors.BOLD}What is Manual Mode?{Colors.ENDC}\n"
               "Manual mode lets you provide your own software idea details. Perfect\n"
               "when you know exactly what you want to build.\n\n"
               f"{Colors.BOLD}Basic Usage (Title Only):{Colors.ENDC}\n"
               "python main.py manual \"My Awesome Tool\"\n\n"
               f"{Colors.BOLD}Full Options:{Colors.ENDC}\n"
               "python main.py manual \"Task Manager\" \\\n"
               "  --description \"A CLI tool for managing daily tasks\" \\\n"
               "  --slug my-task-cli \\\n"
               "  --tech_stack \"Python,Click,SQLite\" \\\n"
               "  --features \"CRUD operations,Priority tags,Export CSV\" \\\n"
               "  --watch\n\n"
               f"{Colors.BOLD}Required Inputs:{Colors.ENDC}\n"
               "• title         Project name (positional argument)\n\n"
               f"{Colors.BOLD}Optional Inputs:{Colors.ENDC}\n"
               "• --description  Detailed project description (defaults to title)\n"
               "• --slug         Custom repository name (auto-generated if omitted)\n"
               "• --tech_stack   Comma-separated list of technologies\n"
               "• --features     Comma-separated list of key features\n"
               "• --private      Create private repository (default: public)\n"
               "• --watch        Watch session until completion\n\n"
               f"{Colors.BOLD}Tips:{Colors.ENDC}\n"
               "• Slugs are auto-generated in kebab-case from title\n"
               "• Very long titles (>100 chars) are handled gracefully\n"
               "• Tech stack and features help guide the scaffolding\n"
               "• If title is very long, it's used as description\n\n"
               f"{Colors.BOLD}What Happens Next?{Colors.ENDC}\n"
               "1. Your idea details are validated\n"
               "2. GitHub repository is created with MVP scaffold\n"
               "3. Jules session starts with automated development\n"
               "4. (Optional) Watch progress until PR is created")

    print("")
    print_panel(
        content,
        title="✍️  Manual Mode Guide",
        color=Colors.GREEN,
        width=70)
    print("")


def print_examples() -> None:
    """Display common usage examples."""

    content = (f"{Colors.BOLD}Quick Start - Generate Random Idea:{Colors.ENDC}\n"
               "python main.py agent\n\n"
               f"{Colors.BOLD}Generate CLI Tool with Auto-Watch:{Colors.ENDC}\n"
               "python main.py agent --category cli_tool --watch\n\n"
               f"{Colors.BOLD}Extract Idea from Website:{Colors.ENDC}\n"
               "python main.py website --url https://news.ycombinator.com/item?id=12345\n\n"
               f"{Colors.BOLD}Manual Entry - Minimal:{Colors.ENDC}\n"
               "python main.py manual \"Budget Tracker\"\n\n"
               f"{Colors.BOLD}Manual Entry - Detailed:{Colors.ENDC}\n"
               "python main.py manual \"Smart Home Dashboard\" \\\n"
               "  --description \"Real-time IoT device monitoring and control\" \\\n"
               "  --tech_stack \"React,Node.js,WebSockets,PostgreSQL\" \\\n"
               "  --features \"Device monitoring,Alert system,Usage analytics\" \\\n"
               "  --private --watch\n\n"
               f"{Colors.BOLD}Check Session Status:{Colors.ENDC}\n"
               "python main.py status <session_id>\n\n"
               f"{Colors.BOLD}Watch Existing Session:{Colors.ENDC}\n"
               "python main.py status <session_id> --watch\n\n"
               f"{Colors.BOLD}List Available Sources:{Colors.ENDC}\n"
               "python main.py list-sources")

    print("")
    print_panel(
        content,
        title="📚 Usage Examples",
        color=Colors.HEADER,
        width=70)
    print("")
