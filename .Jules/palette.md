## 2024-05-20 - CLI Spinners
**Learning:** Python CLIs benefit significantly from threaded spinners for synchronous blocking operations. Simple `print` loops feel unresponsive.
**Action:** Use the new `Spinner` class in `src/utils/reporter.py` for any future long-running tasks.

## 2026-01-03 - Accessible Interactivity on Dark Mode Landing Pages
**Learning:** In dark-themed landing pages with custom interactions (like command tabs or copy buttons), standard accessibility roles (tablist, tabpanel) and visual focus indicators (`:focus-visible`) are often overlooked but critical for making high-tech designs usable for everyone.
**Action:** Always implement a "Skip to Content" link and ensure custom UI components like tabs have correct ARIA roles and update states dynamically in JS.
