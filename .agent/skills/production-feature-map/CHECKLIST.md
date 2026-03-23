# Production Feature Map — Checklist

> Living backlog for `jules-idea-automation`. Covers both **the tool itself** and **the repositories it generates**.

---

## Part A: The Tool (`jules-idea-automation`)

### A1. Error Handling & Resilience

- [ ] **P0** — **Graceful API failure recovery in workflow**: If GitHub repo creation succeeds but Jules session creation fails, the CLI should report the partial success (repo URL) and suggest `status` command. Currently the session errors may leave the user with no repo URL output.
  - *Acceptance*: Partial success prints repo URL + clear next-step guidance. Test with mock Jules timeout.
  - *Affected*: `src/core/workflow.py` → `execute()`

- [ ] **P1** — **Retry with backoff on GitHub API calls**: `GitHubClient.create_repo` and `create_files` have no retry logic. 5xx from GitHub loses the entire workflow.
  - *Acceptance*: All GitHub API calls retry up to 3× with exponential backoff. Unit test with mock 502 response.
  - *Affected*: `src/services/github.py`

- [ ] **P1** — **Retry with backoff on Jules API calls**: `JulesClient.create_session`, `get_session`, `list_activities` have no retry. 5xx from Jules is unrecoverable.
  - *Acceptance*: All Jules API calls retry up to 3× with exponential backoff. Unit test with mock 503 response.
  - *Affected*: `src/services/jules.py`

- [ ] **P2** — **Structured error output for all CLI commands**: When any command fails, the user should see a clear error panel with the error type, message, and actionable tip — not a raw traceback.
  - *Acceptance*: Top-level `try/except` in `main.py` catches `AppError` subclasses and prints formatted panels. Tracebacks only in `--verbose` mode.
  - *Affected*: `main.py`, `src/utils/errors.py`

- [ ] **P2** — **Network connectivity pre-check**: Before starting any workflow, ping the three APIs (Gemini, GitHub, Jules) to fail fast with a clear message instead of failing mid-workflow.
  - *Acceptance*: `--preflight` flag or automatic check at workflow start. Prints which services are reachable.
  - *Affected*: `src/core/workflow.py`, `src/cli/commands.py`

---

### A2. Testing & Quality

- [ ] **P0** — **Integration test for full workflow** (`execute()`): No test exercises the `IdeaWorkflow.execute()` path end-to-end with mocked services.
  - *Acceptance*: `tests/core/test_workflow.py` exists with at least 3 scenarios: happy path, partial failure (Jules down), scaffold failure (fallback used). All mocked.
  - *Affected*: `tests/core/test_workflow.py` (new)

- [ ] **P1** — **Test coverage gate in CI**: CI runs tests but has no minimum coverage threshold.
  - *Acceptance*: `pytest-cov` added to dev deps. CI fails if coverage drops below 70%. Coverage report uploaded as artifact.
  - *Affected*: `.github/workflows/ci.yml`, `pyproject.toml`

- [ ] **P1** — **Test the audit logger**: `JsonFileAuditLogger` has no dedicated tests. Atomic write and error cases are untested.
  - *Acceptance*: `tests/services/test_audit.py` with happy path, write failure, and concurrent write tests.
  - *Affected*: `tests/services/test_audit.py` (new)

- [ ] **P2** — **Test the event bus**: `LocalEventBus` has only an integration test. No unit tests for subscribe/publish edge cases (duplicate handler, error in handler).
  - *Acceptance*: `tests/services/test_bus.py` with edge case coverage.
  - *Affected*: `tests/services/test_bus.py` (new)

- [ ] **P2** — **Test the cache provider**: `FileCacheProvider` has an integration test but no unit tests for corruption, expiry, or race conditions.
  - *Acceptance*: `tests/services/test_cache.py` with corruption recovery and missing dir tests.
  - *Affected*: `tests/services/test_cache.py` (new)

- [ ] **P3** — **Property-based tests for slugify**: The slugify utility handles edge cases (unicode, long strings) but has no property-based testing.
  - *Acceptance*: `hypothesis` tests ensuring output is always valid kebab-case ≤100 chars.
  - *Affected*: `tests/utils/test_slugify.py` (new)

---

### A3. Configuration & Environment

- [ ] **P0** — **Startup config validation**: The tool only validates API keys when the respective client is first used. Missing keys should be caught at startup with a clear checklist of what's wrong.
  - *Acceptance*: `main.py` validates all 3 env vars (`GEMINI_API_KEY`, `GITHUB_TOKEN`, `JULES_API_KEY`) before dispatching any command. Prints a table of missing/present keys.
  - *Affected*: `main.py`, `src/cli/commands.py`

- [ ] **P1** — **Config file support** (`.julesrc` or `pyproject.toml` `[tool.jules]`): Allow default flags (e.g., `--public`, `--timeout 900`) to be set in a config file so users don't repeat them.
  - *Acceptance*: Config loading from `~/.julesrc` or `pyproject.toml [tool.jules]`. CLI flags override config values.
  - *Affected*: `src/cli/parser.py`, new `src/utils/config.py`

- [ ] **P2** — **GitHub organization support**: Currently only creates repos under the authenticated user. Should support `--org` flag.
  - *Acceptance*: `--org` flag on `agent`, `website`, and `manual` commands. Repos created under the specified org.
  - *Affected*: `src/cli/parser.py`, `src/services/github.py`, `src/core/workflow.py`

- [ ] **P2** — **Custom Gemini model override**: Allow `--model` flag to override the default model list for experimentation.
  - *Acceptance*: `--model` flag accepted. Passed through to `GeminiClient`. Validated against known model patterns.
  - *Affected*: `src/cli/parser.py`, `src/services/gemini.py`

---

### A4. Observability & Logging

- [ ] **P1** — **Structured JSON logging**: The tool uses `logging` with default formatting. Production use needs structured JSON logs for debuggability.
  - *Acceptance*: `--log-format json` flag. Default stays human-readable. JSON format includes timestamp, level, module, message.
  - *Affected*: `main.py`, new `src/utils/logging.py`

- [ ] **P1** — **Workflow correlation IDs**: Each `execute()` run should generate a UUID that appears in all log messages and the audit log for traceability.
  - *Acceptance*: Correlation ID set at workflow start. Visible in logs, audit JSONL entries, and final report.
  - *Affected*: `src/core/workflow.py`, `src/services/audit.py`

- [ ] **P2** — **Timing instrumentation**: Report how long each phase takes (Gemini generation, GitHub creation, Jules indexing, scaffold commit) in the final report.
  - *Acceptance*: Each step timed. Final report shows duration per step. Audit log includes timings.
  - *Affected*: `src/core/workflow.py`, `src/utils/reporter.py`

- [ ] **P3** — **API call counter**: Track and report total API calls made per workflow run (useful for cost monitoring).
  - *Acceptance*: Counter incremented per HTTP call. Printed in verbose output and audit log.
  - *Affected*: `src/services/gemini.py`, `src/services/github.py`, `src/services/jules.py`

---

### A5. CLI UX & Polish

- [ ] **P1** — **`--dry-run` mode**: Execute everything except actual API calls. Show what would be created (repo name, files, session params).
  - *Acceptance*: `--dry-run` flag on all three modes. Prints planned actions without side effects. Tests verify no HTTP calls.
  - *Affected*: `src/cli/parser.py`, `src/cli/commands.py`, `src/core/workflow.py`

- [ ] **P1** — **`--verbose` / `--quiet` flags**: Currently hardcoded `verbose=True`. Should support silent mode for scripting.
  - *Acceptance*: `--verbose` shows debug output. `--quiet` suppresses everything except the final report JSON. Default stays as-is.
  - *Affected*: `src/cli/parser.py`, `main.py`, `src/core/workflow.py`

- [ ] **P2** — **JSON output mode**: `--output json` for piping into other tools. The final `WorkflowResult` printed as JSON instead of panels.
  - *Acceptance*: `--output json` flag. Outputs `WorkflowResult.model_dump_json()`. No panels or spinners when active.
  - *Affected*: `src/cli/parser.py`, `src/cli/commands.py`

- [ ] **P2** — **Confirmation prompt before repo creation**: For non-scripted use, ask "Create repo 'my-tool'? [Y/n]" before making irreversible API calls.
  - *Acceptance*: Interactive confirmation by default. `--yes` flag to skip. Respects `--quiet` mode.
  - *Affected*: `src/cli/commands.py`, `src/core/workflow.py`

- [ ] **P3** — **Shell completion**: Bash/Zsh/Fish completion scripts for commands, flags, and category values.
  - *Acceptance*: `python main.py --install-completion` generates shell completion. Tab-complete works for commands and `--category` values.
  - *Affected*: `src/cli/parser.py` or new completion script

---

### A6. Security Hardening

- [ ] **P1** — **Token scope validation**: Verify the GitHub token has `repo` scope at startup. Currently fails mid-workflow with a confusing 404.
  - *Acceptance*: `GitHubClient.__init__` checks token scopes via `GET /user` headers. Raises `ConfigurationError` with tip if missing.
  - *Affected*: `src/services/github.py`

- [ ] **P2** — **Secrets scanning in CI**: Ensure no secrets are accidentally committed. Add `trufflehog` or `gitleaks` to CI.
  - *Acceptance*: Secret scanning job in `.github/workflows/security.yml`. Fails PR on detected secrets.
  - *Affected*: `.github/workflows/security.yml`

- [ ] **P2** — **Rate limit awareness**: GitHub API rate limits (5000/hr) should be checked and reported proactively, not discovered mid-batch.
  - *Acceptance*: Check `X-RateLimit-Remaining` header after each call. Warn when below 100. Pause when exhausted.
  - *Affected*: `src/services/github.py`

---

### A7. Data & Persistence

- [ ] **P1** — **SQLite tracking database** (from roadmap Phase 3): Track all generated repos, session IDs, statuses, and PR URLs in a local SQLite database.
  - *Acceptance*: `~/.jules/history.db` created on first run. Schema: `(id, slug, repo_url, session_id, session_url, pr_url, status, created_at)`. `list` command queries it.
  - *Affected*: New `src/services/db.py`, `src/cli/commands.py` (new `list` command), `src/core/workflow.py`

- [ ] **P2** — **`list` command**: List all previously generated repos with their session statuses.
  - *Acceptance*: `python main.py list` shows a table of all tracked repos. `--status running` filters.
  - *Affected*: `src/cli/parser.py`, `src/cli/commands.py`, `src/services/db.py`

- [ ] **P2** — **History export**: Export audit history as CSV or JSON.
  - *Acceptance*: `python main.py export --format csv > history.csv` works. Reads from SQLite or JSONL.
  - *Affected*: `src/cli/commands.py`, new `src/utils/exporter.py`

- [ ] **P3** — **Cache TTL and cleanup**: `FileCacheProvider` caches indefinitely. Add TTL-based expiry and a `cache clear` command.
  - *Acceptance*: Cache entries older than 24h ignored. `python main.py cache clear` deletes all cached responses.
  - *Affected*: `src/services/cache.py`, `src/cli/parser.py`, `src/cli/commands.py`

---

### A8. Deployment & Distribution

- [ ] **P1** — **PyPI-ready packaging**: The tool should be installable via `pip install jules-idea-automation` with a proper entry point.
  - *Acceptance*: `pyproject.toml` has `[project.scripts]` entry. `pip install .` works. `jules` command available globally.
  - *Affected*: `pyproject.toml`

- [ ] **P2** — **Docker image**: Containerized version for CI/CD pipelines and users who don't want to install Python.
  - *Acceptance*: `Dockerfile` with slim Python base. `.env` mounted via volume. `docker run jules agent` works.
  - *Affected*: New `Dockerfile`, new `.dockerignore`

- [ ] **P2** — **GitHub Release automation**: Tag-based releases with changelog and PyPI publish.
  - *Acceptance*: Pushing a `v*` tag triggers CI to build and publish to PyPI. Release notes auto-generated.
  - *Affected*: New `.github/workflows/release.yml`

---

### A9. Input Modes

- [x] **P1** — **Paste-content command** (`jules paste`): New command that accepts raw text content directly — pasted, piped via stdin, or read from a file — and feeds it to Gemini for idea extraction. Bypasses the web scraper entirely. Solves the common problem where corporate privacy/security tools block URL scraping.
  - *Acceptance*: `jules paste` opens an interactive prompt where the user pastes content and presses Ctrl-D (or Enter twice) to submit. `jules paste --file page.txt` reads from a file. `cat page.html | jules paste -` reads from stdin. Content is passed to `gemini.extract_idea_from_text()` identically to the `website` command's scraped output. All three input methods tested.
  - *Affected*: `src/cli/parser.py` (new `paste` subcommand with `--file` arg), `src/cli/commands.py` (new `handle_paste` handler), `src/utils/reporter.py` (paste-mode prompt UX)

- [x] **P2** — **`--content` flag on `website` command**: Allow `jules website --content "..."` to provide the page content inline, skipping the scrape step. Useful for quick one-liners or when the user has already copied the text.
  - *Acceptance*: `jules website --content "Some page text..."` bypasses `scrape_text()` and goes straight to `gemini.extract_idea_from_text()`. Mutually exclusive with `--url`. Tests verify scraper is never called when `--content` is provided.
  - *Affected*: `src/cli/parser.py` (new `--content` on website), `src/cli/commands.py` → `handle_website()`

---

## Part B: Generated Repositories

### B1. Scaffold Quality & Language Support

- [ ] **P1** — **Language-aware scaffolding**: Currently only generates Python scaffolds (main.py, src/, tests/). Should detect `tech_stack` and generate appropriate structure (Node.js → package.json, Go → go.mod, etc.).
  - *Acceptance*: When `tech_stack` includes "Node.js" or "Next.js", scaffold uses `package.json`, `src/`, `__tests__/`. At least Python and Node.js supported.
  - *Affected*: `src/services/gemini.py` (prompt), `src/core/models.py` (new scaffolds), `src/templates/` (new template dirs)

- [ ] **P1** — **Scaffold validation**: Verify generated scaffold files are syntactically valid before committing (e.g., Python files parse, JSON is valid).
  - *Acceptance*: `ast.parse()` on Python files, `json.loads()` on JSON files. Invalid files logged and skipped.
  - *Affected*: `src/core/workflow.py` → `_prepare_scaffold_files()`

- [ ] **P2** — **Iterative scaffold generation** (from roadmap Phase 4): Break large scaffolds into multiple smaller Gemini API calls to avoid token limits and timeouts.
  - *Acceptance*: Projects with >12 files split into batches. Each batch committed separately. Total files reported.
  - *Affected*: `src/services/gemini.py`, `src/core/workflow.py`

- [ ] **P2** — **Fallback templates per language**: Current fallback only generates Python. Node.js, Go, and Rust fallback templates needed.
  - *Acceptance*: `src/templates/scaffold/` has subdirs per language. `create_fallback_scaffold` accepts a `language` param.
  - *Affected*: `src/core/models.py`, `src/templates/scaffold/`

---

### B2. CI/CD Injection

- [ ] **P1** — **GitHub Actions CI workflow injection**: Every generated repo should include a working `.github/workflows/ci.yml` that runs tests on push.
  - *Acceptance*: CI workflow template for Python (pytest) and Node.js (jest). Tests run on push and PR. Visible in scaffold output.
  - *Affected*: `src/services/gemini.py` (prompt), new `src/templates/scaffold/github_ci.yml.tpl`

- [ ] **P2** — **Pre-commit hook injection**: Generated repos should include a `.pre-commit-config.yaml` with linting and formatting.
  - *Acceptance*: Python repos get ruff + black. Node repos get eslint + prettier. Configured and documented in README.
  - *Affected*: New template files, `src/services/gemini.py` (prompt update)

- [ ] **P3** — **Dependabot injection**: Generated repos should include `dependabot.yml` for automated dependency updates.
  - *Acceptance*: `.github/dependabot.yml` appropriate to detected language. Weekly update schedule.
  - *Affected*: New template file, `src/core/workflow.py` or `gemini.py` prompt

---

### B3. README & Documentation Quality

- [ ] **P1** — **Richer README generation**: Current README is basic. Should include badges, setup instructions, architecture section, and contributing guidelines.
  - *Acceptance*: README includes: build status badge, tech stack badges, quick start section, environment setup, project structure, and license.
  - *Affected*: `src/core/readme_builder.py`

- [ ] **P2** — **API documentation placeholder**: For `api_service` category repos, generate an OpenAPI stub or API docs section.
  - *Acceptance*: API repos include `docs/api.md` with endpoint placeholder structure.
  - *Affected*: `src/services/gemini.py` (prompt), `src/core/readme_builder.py`

- [ ] **P3** — **CONTRIBUTING.md injection**: Every generated repo should include a standard contributor guide.
  - *Acceptance*: Template `CONTRIBUTING.md` added to scaffold. Covers setup, testing, PR conventions.
  - *Affected*: New template file, `src/core/workflow.py`

---

### B4. Development Environment & Handoff

- [ ] **P1** — **Dev container support**: Generated repos should include `.devcontainer/devcontainer.json` for GitHub Codespaces / VS Code.
  - *Acceptance*: Python repos get a Python devcontainer. Node repos get a Node devcontainer. Container starts and tests pass.
  - *Affected*: New template files, scaffold generation prompt

- [ ] **P2** — **Environment validation script**: Generated repos should include a `scripts/check-env.sh` that verifies all runtime dependencies are installed.
  - *Acceptance*: Script checks Python version, required env vars, and dependency installation. Exits with clear error messages.
  - *Affected*: New template file, scaffold generation

- [ ] **P2** — **Docker Compose for local development**: For repos with databases (PostgreSQL, Redis), generate a `docker-compose.yml` for one-command local setup.
  - *Acceptance*: When tech stack includes DB, `docker-compose.yml` with service definitions is generated. `docker compose up` starts all services.
  - *Affected*: `src/services/gemini.py` (prompt), new template

- [ ] **P3** — **IDE configuration injection**: Generate `.vscode/settings.json` and `.vscode/extensions.json` with language-appropriate linter/formatter extensions.
  - *Acceptance*: VS Code settings for Python (ruff, mypy) or Node (eslint, prettier) included. Extensions recommended.
  - *Affected*: New template files

---

*Last updated: 2026-03-23*
