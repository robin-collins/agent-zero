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
- `SCREEN-SHOTS.md` - **NEW** Original screenshot analysis report
- `SCREENSHOTS-ENHANCED.md` - **NEW** Enhanced screenshot implementation report

## GitHub Actions Directory (`.github/workflows/`)
- `build-containers.yml` - **NEW** Container image build workflow for GHCR

## Python Tools Directory (`python/tools/`)
- `behaviour_adjustment.py` - Dynamic behavior modification
- `browser_agent.py` - Web browser automation
- `browser_agent_enhanced.py` - **NEW** Enhanced browser agent with screenshot system
- `call_subordinate.py` - Multi-agent delegation
- `code_execution_tool.py` - Python/Node.js/Shell execution
- `document_query.py` - Document analysis and Q&A
- `email_manager.py` - Email IMAP/SMTP operations
- `calendar_manager.py` - **NEW** CalDAV calendar management
- `screenshot_tool.py` - **NEW** Dedicated screenshot capture tool
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
- `migrate_browser_agent.py` - **NEW** Migration utility for browser agent

## Python Helpers Directory (`python/helpers/`)
- `api.py` - API helper functions
- `attachment_manager.py` - File attachment management
- `backup.py` - Backup and restore functionality
- `browser.py` - Browser helper functions
- `browser_use.py` - Browser-use library integration
- `call_llm.py` - LLM calling utilities
- `crypto.py` - Cryptographic functions
- `defer.py` - Deferred task execution
- `dirty_json.py` - JSON parsing utilities
- `docker.py` - Docker integration helpers
- `document_query.py` - Document query utilities
- `dotenv.py` - Environment variable management
- `duckduckgo_search.py` - DuckDuckGo search integration
- `errors.py` - Error handling utilities
- `extension.py` - Extension system helpers
- `extract_tools.py` - Tool extraction utilities
- `faiss_monkey_patch.py` - FAISS library patches
- `file_browser.py` - File browser utilities
- `files.py` - File system utilities
- `git.py` - Git integration helpers
- `history.py` - Conversation history management
- `images.py` - Image processing utilities
- `job_loop.py` - Job processing loop
- `knowledge_import.py` - Knowledge import utilities
- `localization.py` - Localization support
- `log.py` - Logging utilities
- `mcp_handler.py` - MCP protocol handler
- `mcp_server.py` - MCP server implementation
- `memory.py` - Memory management utilities
- `messages.py` - Message handling utilities
- `perplexity_search.py` - Perplexity search integration
- `persist_chat.py` - Chat persistence utilities
- `playwright.py` - Playwright integration
- `print_catch.py` - Print output capture
- `print_style.py` - Print styling utilities
- `process.py` - Process management utilities
- `rate_limiter.py` - Rate limiting utilities
- `rfc.py` - RFC (Remote Function Call) utilities
- `rfc_exchange.py` - RFC exchange management
- `rfc_files.py` - RFC file handling
- `runtime.py` - Runtime utilities
- `searxng.py` - SearXNG search integration
- `settings.py` - Settings management
- `settings_screenshot_integration.py` - **NEW** Screenshot settings integration
- `shell_local.py` - Local shell execution
- `shell_ssh.py` - SSH shell execution
- `strings.py` - String utilities
- `task_scheduler.py` - Task scheduling utilities
- `timed_input.py` - Timed input utilities
- `tokens.py` - Token management utilities
- `tool.py` - Tool base class and utilities
- `tunnel_manager.py` - Tunnel management
- `vector_db.py` - Vector database utilities
- `whisper.py` - Whisper speech recognition

## Python Screenshots System (`python/helpers/screenshots/`)
- `__init__.py` - **NEW** Main screenshot module
- `interfaces/` - **NEW** Screenshot interfaces
  - `__init__.py` - Interface module
  - `screenshot_provider.py` - Provider interface and base classes
- `providers/` - **NEW** Screenshot provider implementations
  - `__init__.py` - Provider module  
  - `playwright_provider.py` - Playwright-based provider
- `managers/` - **NEW** Screenshot management
  - `__init__.py` - Manager module
  - `browser_screenshot_manager.py` - Browser screenshot manager
  - `auto_screenshot_manager.py` - Automatic screenshot manager
- `utils/` - **NEW** Screenshot utilities
  - `__init__.py` - Utilities module
  - `path_utils.py` - Path management utilities
  - `cleanup_utils.py` - Cleanup and maintenance utilities
  - `validation_utils.py` - Validation and sanitization utilities
- `storage/` - **NEW** Screenshot storage
  - `__init__.py` - Storage module
  - `file_storage.py` - File system storage provider

## Prompt Files Directory (`prompts/default/`)
- `agent.system.tools.md` - Master tools registry
- `agent.system.tool.behaviour.md` - Behavior tool prompts
- `agent.system.tool.browser.md` - Browser tool prompts
- `agent.system.tool.call_sub.md` - Subordinate call prompts
- `agent.system.tool.code_exe.md` - Code execution prompts
- `agent.system.tool.document_query.md` - Document query prompts
- `agent.system.tool.email_manager.md` - Email manager prompts
- `agent.system.tool.calendar_manager.md` - **NEW** Calendar manager prompts
- `agent.system.tool.screenshot.md` - **NEW** Screenshot tool prompts
- `agent.system.tool.input.md` - Input tool prompts
- `agent.system.tool.memory.md` - Memory tools prompts
- `agent.system.tool.response.md` - Response tool prompts
- `agent.system.tool.scheduler.md` - Scheduler tool prompts
- `agent.system.tool.search_engine.md` - Search engine prompts

## Tests Directory (`tests/`)
- `screenshots/` - **NEW** Screenshot system tests
  - `__init__.py` - Test module
  - `test_screenshot_provider.py` - Provider tests
  - `test_screenshot_manager.py` - Manager tests
- `mcp/` - MCP server tests and examples
  - `stream_http_mcp_server.py` - HTTP MCP server example
  - `stream_http_mcp_server_README.md` - MCP server documentation
  - `stream_http_mcp_server_requirements.txt` - MCP server dependencies

## Documentation Directory (`docs/`)
- `README.md` - Documentation overview
- `architecture.md` - System architecture documentation
- `contribution.md` - Contribution guidelines
- `cuda_docker_setup.md` - CUDA Docker setup guide
- `installation.md` - Installation instructions
- `mcp_setup.md` - MCP (Model Context Protocol) setup
- `quickstart.md` - Quick start guide
- `screenshots.md` - **NEW** Comprehensive screenshot system documentation
- `troubleshooting.md` - Troubleshooting guide
- `tunnel.md` - Tunnel setup and usage
- `usage.md` - Usage documentation
- `designs/` - Design specifications
  - `backup-specification-backend.md` - Backend backup specification
  - `backup-specification-frontend.md` - Frontend backup specification
- `res/` - Documentation resources (images, videos, etc.)

## Root Level Scripts
- `deploy_screenshot_system.py` - **NEW** Deployment script for screenshot system
- `validate_screenshot_implementation.py` - **NEW** Validation script for implementation

## Recent Changes
- **2024-01-XX**: Added comprehensive screenshot system with modular architecture
  - **Core System**: Complete `python/helpers/screenshots/` module with interfaces, providers, managers, utilities, and storage
  - **Interface Layer**: Abstract provider interface with SOLID principles implementation
  - **Provider Implementation**: Playwright-based provider with comprehensive error handling
  - **Management Layer**: Browser screenshot manager and automatic trigger manager
  - **Utilities**: Path management, cleanup, and validation utilities
  - **Storage System**: File system storage provider with metadata support
  - **Tool Integration**: Dedicated screenshot tool (`screenshot_tool.py`) and enhanced browser agent
  - **Settings Integration**: Complete settings system integration with validation
  - **Migration Support**: Migration utilities and backward compatibility
  - **Documentation**: Comprehensive documentation in `docs/screenshots.md`
  - **Testing**: Full test suite with unit and integration tests
  - **Deployment**: Automated deployment and validation scripts
  - **Quality Assurance**: Comprehensive error handling, validation, and resource management
  - **Enhanced Features**: PNG/JPEG support, quality control, automatic cleanup, metadata storage
  - **Security**: Path validation, sanitization, and resource limits
  - **Performance**: Efficient async operations, cleanup automation, and resource management
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