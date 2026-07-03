# Architecture Decision Log (ADL)

## ADR-001: Layered Architecture
* **Status:** Approved
* **Context:** Keep codebase maintainable, modular, and decoupled.
* **Decision:** Enforce clean separation across strict architectural tiers (UI → API → Service → Database).

## ADR-002: Centralized Configuration
* **Status:** Approved
* **Decision:** `backend/config.py` acts as the exclusive single source of truth using `pydantic-settings`. No other file reads `.env` variables directly.

## ADR-003: Centralized Structured Logging
* **Status:** Approved
* **Decision:** Unified diagnostic instrumentation using Loguru across all modules. Raw `print()` statements are strictly banned.

## ADR-004: Feature-Based API Routing with Versioning
* **Status:** Approved
* **Decision:** Endpoints are organized into distinct files inside `backend/api/` based on feature domains. All business endpoints must inherit the `/api/v1` prefix to ensure professional REST standards.
