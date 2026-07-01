## Why

The current project logging model mixes request timing, model timing, frontend API timing, diagnostic output, and ad-hoc process logs, which creates noise during everyday debugging. Timing logs were useful while optimizing early RAG latency, but they are no longer the primary signal and should not be emitted by default.

This change defines a quieter, explicit logging policy so developers can quickly distinguish startup failures, API errors, frontend request failures, and retrieval-quality diagnostics.

## What Changes

- Introduce a project-wide logging policy that defines log categories, default output locations, and when each category is enabled.
- Replace default `TIMING` request logs with error-first backend logs and optional debug logs.
- Remove the `/api/performance` timing endpoint from the required API contract unless a future profiling mode explicitly reintroduces it.
- Move frontend API timing console output behind a debug flag, while keeping request failures visible.
- Keep retrieval diagnostics as explicit command output and JSON reports, not always-on runtime logs.
- Clarify which logs belong in terminal output, browser console, `logs/`, and diagnostic artifact directories.

## Capabilities

### New Capabilities
- `logging-settings`: Defines the project's runtime logging categories, defaults, output destinations, and debug controls.

### Modified Capabilities
- `api-timing-log`: Backend timing logs and `/api/performance` are no longer required by default and are replaced by optional debug/profiling behavior.
- `frontend-timing-log`: Browser API timing logs are no longer required by default and become optional debug output.

## Impact

- Affected backend files: `app/api/server.py`, `app/api/routers/*`, `app/modules/session/session_manager.py`, and any shared logging helper added later.
- Affected frontend files: `ui/src/api/index.ts` and any environment/config files used to toggle debug logs.
- Affected documentation: `README.md` logging/debug sections and any developer troubleshooting notes.
- Existing diagnostic scripts under `test/` remain explicit tools and should not be treated as runtime logging.
