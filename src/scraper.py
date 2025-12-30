import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from src.utils.security import validate_url, ScrapingError

def scrape_text(url):
    """
    Fetches the content of a URL and extracts the text.
    Uses Playwright for JavaScript rendering support, falls back to requests.
    """
    try:
        # Security: Validate URL to prevent SSRF
        validate_url(url)

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            content = page.content()
            browser.close()

        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except ScrapingError:
        raise
    except Exception as e:
        print(f"Playwright scraping failed: {e}. Falling back to requests.")
        try:
            # Re-validate just in case (though should be redundant if already checked)
            validate_url(url)

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            return text
        except ScrapingError:
            raise
        except Exception as e2:
             raise RuntimeError(f"Failed to scrape URL {url}: {e2}")
