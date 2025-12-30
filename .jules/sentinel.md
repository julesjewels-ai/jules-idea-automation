## 2025-12-30 - SSRF in Unused Code
**Vulnerability:** A legacy/alternate file `src/scraper.py` lacked SSRF protection compared to the main service, exposing the application to internal network scanning if that file were used.
**Learning:** Unused or duplicate code paths often miss security updates applied to the main codebase.
**Prevention:** Centralize security controls (like input validation) in shared utility modules (`src/utils/security.py`) so all consumers, even legacy ones, benefit from the same protection levels.
