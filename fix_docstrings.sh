# Disable the exit on error for this one because some fixes might naturally fail or skip
set +e

# src/cli/parser.py
sed -i 's/Creates the argparse/Create the argparse/' src/cli/parser.py

# src/core/models.py
sed -i 's/Creates a fallback scaffold/Create a fallback scaffold/' src/core/models.py

# src/core/readme_builder.py
sed -i 's/Builds a comprehensive/Build a comprehensive/' src/core/readme_builder.py

# src/utils/errors.py
sed -i '/class AppError(Exception):/a\    """Base error class."""' src/utils/errors.py
sed -i '/def __init__(self, message: str, tip: str | None = None) -> None:/a\        """Initialize the error."""' src/utils/errors.py

# src/utils/polling.py
sed -i 's/Polls a function until/Poll a function until/' src/utils/polling.py

# src/utils/reporter.py
sed -i 's/Removes ANSI color codes/Remove ANSI color codes/' src/utils/reporter.py
sed -i 's/Prints text inside a bordered box/Print text inside a bordered box/' src/utils/reporter.py
sed -i '/def __init__(self, text: str = "Working...") -> None:/a\        """Initialize the spinner."""' src/utils/reporter.py
sed -i '/def __enter__(self) -> "Spinner":/a\        """Enter the context manager."""' src/utils/reporter.py
sed -i '/def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:/a\        """Exit the context manager."""' src/utils/reporter.py
sed -i 's/Prints the main application header/Print the main application header/' src/utils/reporter.py
sed -i 's/Prints the final workflow success report/Print the final workflow success report/' src/utils/reporter.py
sed -i 's/Prints the live status of an ongoing/Print the live status of an ongoing/' src/utils/reporter.py
sed -i 's/Formats a timedelta/Format a timedelta/' src/utils/reporter.py
sed -i 's/Prints a progress indicator/Print a progress indicator/' src/utils/reporter.py
sed -i 's/Prints the completion message/Print the completion message/' src/utils/reporter.py
sed -i 's/Prints a timeout warning/Print a timeout warning/' src/utils/reporter.py
sed -i 's/Prints a list of Jules sources/Print a list of Jules sources/' src/utils/reporter.py
sed -i 's/Prints a summary of the extracted idea/Print a summary of the extracted idea/' src/utils/reporter.py
sed -i 's/Prints a rich demo-mode report/Print a rich demo-mode report/' src/utils/reporter.py

# src/services/scraper.py
sed -i 's/Fetches and extracts text/Fetch and extract text/' src/services/scraper.py
sed -i 's/Extracts visible text/Extract visible text/' src/services/scraper.py
sed -i 's/Fetches the URL/Fetch the URL/' src/services/scraper.py

# src/services/http_client.py
sed -i '/def __init__(/a\        """Initialize the base API client."""' src/services/http_client.py

# src/services/gemini.py
sed -i '/"""Gemini API client/i\"""Gemini API client module."""' src/services/gemini.py
sed -i '/def __init__(self, models: list\[str\] | None = None, api_key: str | None = None) -> None:/a\        """Initialize the Gemini client."""' src/services/gemini.py
sed -i 's/Maps Google GenAI API errors/Map Google GenAI API errors/' src/services/gemini.py
sed -i 's/Checks if content is cached/Check if content is cached/' src/services/gemini.py
sed -i 's/Parses JSON from Gemini/Parse JSON from Gemini/' src/services/gemini.py
sed -i 's/Fetches content from Gemini API/Fetch content from Gemini API/' src/services/gemini.py
sed -i 's/Helper to run/Run/' src/services/gemini.py
sed -i 's/Generates a software idea/Generate a software idea/' src/services/gemini.py
sed -i 's/Extracts an idea/Extract an idea/' src/services/gemini.py
sed -i 's/Generates a project scaffold/Generate a project scaffold/' src/services/gemini.py

# src/services/jules.py
sed -i '/def __init__(self, api_key: str | None = None) -> None:/a\        """Initialize the Jules client."""' src/services/jules.py
sed -i 's/Lists existing codebase sources/List existing codebase sources/' src/services/jules.py
sed -i 's/Creates a new Jules session/Create a new Jules session/' src/services/jules.py
sed -i 's/Checks if a source exists/Check if a source exists/' src/services/jules.py
sed -i 's/Retrieves session details/Retrieve session details/' src/services/jules.py
sed -i 's/Lists all sessions/List all sessions/' src/services/jules.py
sed -i 's/Lists recent activities/List recent activities/' src/services/jules.py
sed -i 's/Sends a message to a session/Send a message to a session/' src/services/jules.py
sed -i 's/Checks if a session has finished/Check if a session has finished/' src/services/jules.py

# src/services/db.py
sed -i '/def __init__(self, db_path: str = ".jules\/history.db") -> None:/a\        """Initialize the history DB."""' src/services/db.py

# src/services/github.py
sed -i '/def __init__(self, token: str | None = None) -> None:/a\        """Initialize the GitHub client."""' src/services/github.py
sed -i 's/Gets the authenticated user/Get the authenticated user/' src/services/github.py
sed -i 's/Creates a new private/Create a new private/' src/services/github.py
sed -i 's/Creates a single file/Create a single file/' src/services/github.py
sed -i 's/Creates multiple files/Create multiple files/' src/services/github.py
