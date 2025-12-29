# Roadmap: Jules Automation Tool

Future improvements to implement in the "idea to repository" automation workflow.

## ✅ Phase 1: Enhanced Session Tracking (COMPLETE)
- [x] Add `get_session(session_id)` to JulesClient
- [x] Add `list_activities(session_id)` to JulesClient  
- [x] Add `--watch` flag to poll for session completion
- [x] Retrieve and print PR URL when available
- [x] Add `status` command to check session progress

## ✅ Phase 3: Better Initial Repository Setup (COMPLETE)
- [x] Generate MVP scaffold with Gemini
- [x] Create modular src/ structure following SOLID principles
- [x] Add batch file creation via Git Data API
- [x] Keep main.py clean - orchestration only

## Phase 4: Enhanced Reporting (Priority: Low)
- [ ] Generate Markdown summary files
- [ ] Include activity log from Jules
- [ ] Add timestamps and duration tracking
