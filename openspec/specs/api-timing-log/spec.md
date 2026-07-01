## Purpose

Backend timing logs have been removed from the default runtime behavior. Request-level timing is now available only through opt-in debug/profiling logging as defined by the logging-settings capability.

## History

The following requirements were removed as part of the `redesign-logging-settings` change:

### ~Requirement: System SHALL log request timing automatically~

Every HTTP request SHALL be logged with its processing time.  
**Removed**: Automatic timing logs added noise during normal debugging and are no longer required by the runtime logging policy.

### ~Requirement: System SHALL track Ollama call timing~

Ollama Embedding and Chat calls SHALL be individually timed.  
**Removed**: Always-on model call timing is a profiling concern, not a default runtime logging requirement. Use explicit profiling or diagnostic tooling for model latency investigations.

### ~Requirement: API SHALL provide performance endpoint~

The system SHALL expose `GET /api/performance` returning recent request timings.  
**Removed**: The `/api/performance` endpoint existed only to support the removed timing collector and is no longer part of the default API contract. Use future explicit profiling tooling if performance summaries are needed.
