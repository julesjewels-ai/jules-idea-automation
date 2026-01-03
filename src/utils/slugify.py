import re

def slugify(text: str, max_length: int = 100) -> str:
    """
    Convert text to a kebab-case slug.
    Example: "My Awesome Tool" -> "my-awesome-tool"
    Enforces a maximum length (default 100 for GitHub).
    """
    # Convert to lowercase
    text = text.lower()
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate to max_length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
        
    return text
