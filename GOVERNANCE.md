# Governance — Automatr Prompt

## Scope

Local-model prompt optimizer desktop application:
- Template CRUD (create, read, update, delete) with JSON-based storage
- Variable substitution and prompt rendering
- llama.cpp LLM runtime management (server lifecycle, model downloads, model selection)
- Local text generation with no network dependency beyond localhost llama-server

## Non-Goals

- Espanso or text-expander integration (see [automatr-espanso](https://github.com/josiahH-cf/automatr-espanso))
- Cloud LLM APIs (OpenAI, Anthropic, etc.)
- Multi-tenant or multi-user access
- Mobile or web deployment
- PyPI publishing

## Architecture Constraints

- **Framework:** PyQt6 desktop application
- **Network:** No internet access required at runtime — all LLM communication is localhost (`llama-server`)
- **Storage:** JSON-only template format; user config stored in platform-specific config directories
- **Models:** GGUF format via llama.cpp; no proprietary model formats

## Deployment Model

Single-user desktop install:
- Recommended: `./install.sh` (creates venv, installs dependencies, downloads llama.cpp)
- Alternative: `pip install -e .` for development
- No containerization, no cloud infrastructure

## Ownership

- Solo maintainer project
- Cross-agent code review encouraged (use a different model than the one that wrote the code)
- Contributions welcome via pull requests

## Roadmap Structure

- Milestones tracked in `/tasks/`
- Feature specs in `/specs/`
- Architectural decisions in `/decisions/`
- See `AGENTS.md` for conventions on planning, testing, and commits
