## REMOVED Requirements

### Requirement: System SHALL log request timing automatically
**Reason**: Always-on request timing logs add noise during normal debugging and are no longer required by the runtime logging policy.
**Migration**: Use the optional backend debug/profiling logging mode when request-level timing is needed.

### Requirement: System SHALL track Ollama call timing
**Reason**: Always-on model call timing is a profiling concern, not a default runtime logging requirement.
**Migration**: Use explicit profiling or diagnostic tooling for model latency investigations.

### Requirement: API SHALL provide performance endpoint
**Reason**: `/api/performance` exposes data that only existed to support the removed timing collector and is no longer part of the default API contract.
**Migration**: Remove calls to `GET /api/performance`; use future explicit profiling tooling if performance summaries are needed.
