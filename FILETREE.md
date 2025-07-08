# File Tree Structure

This document tracks the current file structure of the Agent Zero project, updated as new files are added or modified.

## Root Level
- `agent.py` - Core agent implementation
- `models.py` - LLM model integrations
- `initialize.py` - Framework initialization
- `run_ui.py` - Main Flask web server
- `run_cli.py` - Legacy CLI interface (deprecated)
- `run_tunnel.py` - Tunnel service for remote access
- `requirements.txt` - Python dependencies
- `example.env` - Environment configuration template
- `CHANGELOG.md` - Project changelog (tracks changes)
- `FILETREE.md` - This file structure documentation
- `CONTRIBUTE-TOOLS.md` - Tool development guide

## GitHub Actions Directory (`.github/workflows/`)
- `build-containers.yml` - **NEW** Container image build workflow for GHCR

## Python Tools Directory (`python/tools/`)
- `behaviour_adjustment.py` - Dynamic behavior modification
- `browser_agent.py` - Web browser automation
- `call_subordinate.py` - Multi-agent delegation
- `code_execution_tool.py` - Python/Node.js/Shell execution
- `document_query.py` - Document analysis and Q&A
- `email_manager.py` - Email IMAP/SMTP operations
- `calendar_manager.py` - **NEW** CalDAV calendar management
- `input.py` - Keyboard input simulation
- `memory_delete.py` - Memory deletion operations
- `memory_forget.py` - Memory forgetting operations
- `memory_load.py` - Memory retrieval operations
- `memory_save.py` - Memory storage operations
- `response.py` - Final response output
- `scheduler.py` - Task scheduling and management
- `search_engine.py` - Web search via SearXNG
- `unknown.py` - Fallback for undefined tools
- `vision_load.py` - Image processing and vision

## Prompt Files Directory (`prompts/default/`)
- `agent.system.tools.md` - Master tools registry
- `agent.system.tool.behaviour.md` - Behavior tool prompts
- `agent.system.tool.browser.md` - Browser tool prompts
- `agent.system.tool.call_sub.md` - Subordinate call prompts
- `agent.system.tool.code_exe.md` - Code execution prompts
- `agent.system.tool.document_query.md` - Document query prompts
- `agent.system.tool.email_manager.md` - Email manager prompts
- `agent.system.tool.calendar_manager.md` - **NEW** Calendar manager prompts
- `agent.system.tool.input.md` - Input tool prompts
- `agent.system.tool.memory.md` - Memory tools prompts
- `agent.system.tool.response.md` - Response tool prompts
- `agent.system.tool.scheduler.md` - Scheduler tool prompts
- `agent.system.tool.search_engine.md` - Search engine prompts

## Recent Changes
- **2024-01-XX**: Added GitHub Actions workflow for container image building
  - New file: `.github/workflows/build-containers.yml`
  - Supports manual trigger for building base and main container images
  - Multi-platform support (linux/amd64, linux/arm64)
  - Builds images to GitHub Container Registry (ghcr.io)
  - Configurable branch selection and dependency handling
- **2024-01-XX**: Added CalDAV calendar management tool with comprehensive event management capabilities
  - New files: `calendar_manager.py`, `agent.system.tool.calendar_manager.md`
  - Updated: `agent.system.tools.md` to include calendar manager tool
  - Supports create, read, update, delete operations for calendar events
  - Multi-calendar and timezone support
  - Event search functionality

---

*Note: This file is maintained to track project structure changes. Update when adding, removing, or significantly modifying files.*