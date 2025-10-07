# Local Server Component (planned)

This component will expose selected functionality from the AGC application over a local server so that other devices on the same network can send requests. This document outlines the intended scope and design at a high level. No implementation is provided yet.

## Goals
- Provide a lightweight HTTP (or WebSocket) interface for remote control and status queries
- Run locally alongside the main app with minimal configuration
- Authenticate requests originating from trusted devices on the local network
- Enforce clear separation between API boundary and internal modules

## Non-Goals (initial phase)
- Cloud exposure or remote tunneling
- Long-term stateful session management
- Complex rate limiting or quotas

## Proposed Endpoints (subject to change)
- `GET /health`: Liveness/readiness checks
- `GET /status`: Summary of current app state (voice input status, last analysis timestamp, etc.)
- `POST /command`: Submit a high-level command (e.g., "read options", "select option N")
- `POST /screenshot/analyze`: Trigger a one-off analysis

## Security Considerations
- Bind only to localhost by default; optional LAN exposure via explicit config
- Require a shared secret or token for all non-health endpoints
- Log all requests and decisions with minimal PII

## Integration Points
- Calls into `src/voice_input/` for command handling paths
- Invokes `src/screen_capture/` for on-demand analysis
- Uses `src/ai_agent/` for interpretation and response generation

## Configuration
- Add configuration surface in `src/config/settings.py` (e.g., `LOCAL_SERVER_ENABLED`, `LOCAL_SERVER_HOST`, `LOCAL_SERVER_PORT`, `LOCAL_SERVER_TOKEN`)

## Run (future)
```
python -m src.local_server
```

## Next Steps
- Finalize API surface and request/response schemas
- Pick framework (FastAPI, Flask, or built-in `http.server`) aligning with project standards
- Implement minimal health and status endpoints behind token auth

