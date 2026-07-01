## Context

The project currently has several kinds of output:

- FastAPI/Uvicorn startup and access output.
- Backend ad-hoc `print()` messages, including prior `[TIMING]` messages.
- Frontend browser console messages from `ui/src/api/index.ts`.
- Explicit retrieval diagnostic scripts that print pipeline details and write JSON reports.
- Background process stdout/stderr files under `logs/`.

Timing logs were useful for early latency investigation, but they now make normal debugging harder because routine successful requests produce noise. The new logging design should make errors visible by default, keep optional debug information available, and preserve diagnostic scripts as explicit tools.

## Goals / Non-Goals

**Goals:**

- Establish a quiet default runtime logging mode for both backend and frontend.
- Keep backend startup failures, request failures, and unhandled exceptions visible.
- Make request/debug/profiling output opt-in through clear configuration.
- Keep CLI and retrieval diagnostic outputs explicit and separate from runtime service logs.
- Document where each kind of log should be found during local development.

**Non-Goals:**

- Add an external observability stack, log shipper, tracing system, or metrics database.
- Reintroduce always-on request timing logs.
- Build a production audit-log system.
- Change retrieval diagnostic behavior except to document its boundary.
- Redesign all CLI output into structured logs.

## Decisions

### Use Python standard `logging` for backend application logs

Backend application code should use a lightweight standard-library logger instead of scattered timing `print()` calls. The default level should be `INFO` or `WARNING` depending on local configuration, with errors always emitted.

Rationale: The project is a small Python/FastAPI MVP and does not need an external logging dependency. Standard logging gives levels, formatting, stderr routing, and future file handlers if needed.

Alternative considered: Keep using `print()`. This is simpler but cannot consistently separate debug, info, warning, and error output.

### Keep Uvicorn access logs separate from application debug logs

Uvicorn may still emit server startup and access logs when enabled by the developer, but the application should not add its own duplicate request timing middleware by default.

Rationale: Uvicorn already owns HTTP server logging. Application logs should focus on domain failures and exceptional states.

Alternative considered: Custom middleware for every request. This recreates the removed timing noise and makes normal success paths too chatty.

### Make frontend request success logs opt-in

The frontend API wrapper should continue to surface request failures through `console.error`, but successful `[API]` and `[API][SLOW]` messages should only appear when a Vite debug flag is enabled.

Rationale: Browser consoles should be clean during ordinary development. When debugging API wiring, a single flag can restore request-level visibility.

Alternative considered: Remove all frontend console output. That would hide useful client-side request failures.

### Keep retrieval diagnostics as command-driven artifacts

Scripts such as `test/test_retrieval_diagnostic.py` should remain explicit tools that print detailed stage output and write JSON reports to `test/diagnostic_output/`.

Rationale: Retrieval-quality analysis is verbose by nature and should be invoked when needed, not mixed into service logs.

Alternative considered: Add retrieval-stage logs to every chat request. This would expose too much detail in normal chat flows and make logs hard to scan.

### Use `logs/` only for process-level redirected output

When developers run backend/frontend processes in the background, stdout and stderr should be redirected to `logs/dev-backend.*.log` and `logs/dev-frontend.*.log`. Root-level ad-hoc log files should not be part of the documented route.

Rationale: A single log directory keeps local artifacts predictable and easier to clean.

Alternative considered: Keep root-level `backend.log` and `frontend.log`. This duplicates destinations and makes it unclear which file is authoritative.

## Risks / Trade-offs

- Reduced default visibility can make latency regressions less obvious. Mitigation: keep an explicit debug/profiling flag and retrieval diagnostic scripts.
- Partial migration can leave mixed `print()` and `logging` output. Mitigation: implementation tasks include scanning for runtime `print()` calls and documenting exceptions.
- Frontend debug flags can be forgotten when troubleshooting. Mitigation: document the flag in README and keep request failures visible regardless of the flag.
- Removing `/api/performance` may break manual workflows that still call it. Mitigation: document the removal and keep future profiling as a separate opt-in capability if needed.

## Migration Plan

1. Remove remaining required references to `[TIMING]`, `@timed`, and `/api/performance`.
2. Introduce a small backend logging configuration helper using Python standard `logging`.
3. Convert backend runtime error/status messages to the logger where appropriate.
4. Gate frontend successful API logs behind a Vite environment flag.
5. Update README with the new log route and debug flags.
6. Validate with backend import/compile checks, frontend build, and a smoke test for API failure visibility.

Rollback is straightforward: revert the change files and restore previous API wrapper logging or backend middleware if request timing is needed temporarily.

## Open Questions

- Should the backend default level be `INFO` or `WARNING` for local development?
- Should optional profiling be implemented immediately, or deferred until a concrete latency issue appears?
- Should root-level historical log files be deleted from the repository/workspace or only removed from documentation?
