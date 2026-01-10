## 2024-05-23 - CLI Color Experience
**Learning:** Adding colors to CLI output significantly improves readability and user confidence, especially for error states and success messages. It makes the tool feel more polished and "pro".
**Action:** Use a consistent color palette (Green=Success, Red=Error, Cyan=Info, Yellow=Warning/Tips) across all CLI interactions. Ensure colors are defined in a centralized way (like `Colors` class) for maintainability.

## 2024-05-24 - Visibility of AI Generation
**Learning:** Users trust AI tools more when they can see *what* was generated before an automated action occurs. Silence during "magic" steps creates anxiety about what is happening.
**Action:** Always print a summary of generated content (e.g., Title, Description, key metadata) immediately after generation and before execution. Use formatting to make it scannable.

## 2024-05-25 - Human-Readable Durations
**Learning:** Displaying raw seconds (e.g., "1800s") for long-running processes causes cognitive load as users try to convert to minutes.
**Action:** Always format durations into human-readable strings (e.g., "30m 0s") for any wait time longer than 60 seconds.
