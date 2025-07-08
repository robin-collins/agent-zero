# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Web UI**: `python run_ui.py` - Starts the Flask web server with UI on port 50001 (default)
- **CLI (deprecated)**: `python run_cli.py` - Legacy CLI interface, now discontinued 
- **Tunnel**: `python run_tunnel.py` - Starts tunnel for remote access

### Docker Commands
- **Quick start**: `docker pull frdel/agent-zero-run && docker run -p 50001:80 frdel/agent-zero-run`
- **Development**: `docker build -t agent-zero .` (from docker/run/ directory)
- The framework is designed to run in Docker containers for consistency and security

### Dependencies and Setup
- **Install dependencies**: `pip install -r requirements.txt`
- **Environment setup**: Copy `example.env` to `.env` and configure
- **Initialization**: Run `python initialize.py` for first-time setup

## Architecture Overview

### Core Framework Structure
Agent Zero is a hierarchical multi-agent framework where agents can delegate tasks to subordinate agents. The system consists of:

1. **Agent Hierarchy**: Agent 0 (top-level) can create subordinate agents (A1, A2, etc.) for task delegation
2. **Tools System**: Agents use tools for actions (code execution, web search, memory, browser automation, etc.)
3. **Memory & Knowledge**: Persistent memory with automatic summarization and knowledge base integration
4. **Extension System**: Modular extensions for extending functionality without modifying core code
5. **Prompt-based Configuration**: All behavior defined through markdown prompt files

### Key Components

#### Agent System (`agent.py`)
- `AgentContext`: Manages agent instances and their execution contexts
- `Agent`: Core agent class with monologue loop for reasoning and tool execution
- Multi-agent communication through superior/subordinate relationships
- Real-time streaming with intervention capabilities

#### Models System (`models.py`)
- LiteLLM integration supporting multiple providers (OpenAI, Anthropic, Google, etc.)
- Separate models for chat, utility, embeddings, and browser tasks
- Rate limiting and API key management
- Unified calling interface with streaming support

#### Tools (`python/tools/`)
- **Core Tools**: `response.py`, `code_execution_tool.py`, `search_engine.py`, `call_subordinate.py`
- **Memory Tools**: `memory_save.py`, `memory_load.py`, `memory_delete.py`, `memory_forget.py`
- **Specialized Tools**: `browser_agent.py`, `document_query.py`, `scheduler.py`, `vision_load.py`
- **Behavior**: `behaviour_adjustment.py` for dynamic behavior modification

#### Extensions (`python/extensions/`)
Extensions execute at specific points in the agent's message loop:
- `message_loop_start/`: Executed at the start of each message loop iteration
- `message_loop_prompts_before/` and `message_loop_prompts_after/`: Handle prompt construction
- `monologue_start/` and `monologue_end/`: Executed at monologue boundaries
- `response_stream/` and `reasoning_stream/`: Handle streaming responses

### Configuration and Customization

#### Prompts System (`prompts/`)
All agent behavior is defined through markdown prompt files:
- **Main prompts**: `agent.system.main.*.md` files define core behavior
- **Tool prompts**: `agent.system.tool.*.md` files define individual tool behaviors
- **Framework prompts**: `fw.*.md` files define system messages and responses
- **Custom prompts**: Create subdirectories for custom prompt sets

#### Settings and Configuration
- Settings managed through Web UI or programmatically via `python/helpers/settings.py`
- Configuration includes model settings, API keys, runtime options
- Environment variables loaded from `.env` file

#### Memory System
- **Automatic Memory**: Conversation history with intelligent summarization
- **Persistent Memory**: User-provided information stored in vector database
- **Knowledge Base**: File-based knowledge storage (`knowledge/` directory)
- **Solutions Memory**: Successful solutions saved for future reference

### Docker Runtime
The framework runs in Docker containers with two main images:
- **Base image** (`docker/base/`): Core dependencies and system setup
- **Runtime image** (`docker/run/`): Complete Agent Zero environment
- Persistent volumes for data storage (`/a0` mount point)

### MCP Integration
Model Context Protocol support for:
- **MCP Server**: Agent Zero can act as an MCP server for other tools
- **MCP Client**: Agent Zero can use external MCP servers as tools
- Dynamic tool loading from MCP servers

## Development Guidelines

### Code Organization
- Keep core logic in `agent.py` and `models.py`
- Add new tools as separate files in `python/tools/`
- Use extensions for non-core functionality
- Follow existing patterns for consistency

### Tool Development
1. Create tool class inheriting from `Tool` base class in `python/helpers/tool.py`
2. Add corresponding prompt file in `prompts/default/agent.system.tool.TOOLNAME.md`
3. Reference tool in `prompts/default/agent.system.tools.md`
4. Follow async patterns for tool execution

### Memory and Knowledge
- Use `knowledge/custom/main/` for custom knowledge files
- Memory is automatically managed but can be manually controlled via memory tools
- Support for multiple file formats: PDF, TXT, CSV, HTML, JSON, MD

### Testing and Debugging
- Logs are automatically saved to `logs/` directory as HTML files
- Use the Web UI for interactive debugging and intervention
- Monitor agent reasoning and responses through streaming output

### Security Considerations
- Docker containers provide isolation for code execution
- SSH access for secure remote development environments
- API key management through environment variables
- Basic authentication for web interface

## Detailed Repository Structure

### Root Level Files
- `agent.py`: Core agent implementation and context management
- `models.py`: LLM model integrations and wrappers using LiteLLM
- `initialize.py`: Framework initialization and configuration loading
- `run_ui.py`: Main Flask web server and application entry point
- `run_cli.py`: Legacy CLI interface (deprecated)
- `run_tunnel.py`: Tunnel service for remote access
- `prepare.py`: Environment preparation scripts
- `preload.py`: Pre-initialization routines
- `update_reqs.py`: Dependency update utilities
- `requirements.txt`: Python package dependencies
- `example.env`: Environment configuration template
- `jsconfig.json`: JavaScript configuration for IDE support

### Core Python Directories

#### `python/api/` - REST API Endpoints (39 files)
Web API handlers for all UI functionality:
- **Chat Management**: `chat_load.py`, `chat_remove.py`, `chat_reset.py`, `chat_export.py`
- **Message Handling**: `message.py`, `message_async.py`, `nudge.py`, `pause.py`
- **Settings**: `settings_get.py`, `settings_set.py`, `csrf_token.py`
- **File Operations**: `upload.py`, `download_work_dir_file.py`, `get_work_dir_files.py`
- **Backup/Restore**: `backup_create.py`, `backup_restore.py`, `backup_inspect.py`
- **Scheduler**: `scheduler_task_*.py` files for task management
- **MCP Integration**: `mcp_server_*.py`, `mcp_servers_*.py`
- **System**: `health.py`, `restart.py`, `poll.py`, `transcribe.py`

#### `python/helpers/` - Utility Functions (40 files)
Core framework utilities:
- **Model Integration**: `call_llm.py`, `tokens.py`, `rate_limiter.py`
- **Memory & Knowledge**: `memory.py`, `vector_db.py`, `knowledge_import.py`
- **File Operations**: `files.py`, `file_browser.py`, `attachment_manager.py`
- **Communication**: `messages.py`, `history.py`, `persist_chat.py`
- **System Integration**: `runtime.py`, `settings.py`, `process.py`
- **Docker & SSH**: `docker.py`, `shell_local.py`, `shell_ssh.py`
- **Browser Automation**: `browser.py`, `browser_use.py`, `playwright.py`
- **Search Integration**: `searxng.py`, `duckduckgo_search.py`, `perplexity_search.py`
- **MCP Support**: `mcp_handler.py`, `mcp_server.py`
- **Utilities**: `crypto.py`, `strings.py`, `errors.py`, `log.py`

#### `python/extensions/` - Modular Extensions
Hook-based extension system with execution points:
- **`before_main_llm_call/`**: `_10_log_for_stream.py`
- **`message_loop_start/`**: `_10_iteration_no.py`
- **`message_loop_prompts_before/`**: `_90_organize_history_wait.py`
- **`message_loop_prompts_after/`**: Memory recall, datetime injection, wait handling
- **`message_loop_end/`**: History organization, chat saving
- **`monologue_start/`**: `_60_rename_chat.py`
- **`monologue_end/`**: Memory fragmentation, solution saving, input waiting
- **`reasoning_stream/`**: `_10_log_from_stream.py`
- **`response_stream/`**: Stream logging, live response handling
- **`system_prompt/`**: System prompt construction, behavior injection

#### `python/tools/` - Tool Implementations
**Hardcoded Python Tools** (have both `.py` implementation and `.md` prompt):
- `behaviour_adjustment.py` - Dynamic behavior modification
- `browser_agent.py` - Web browser automation (uses browser-use library)
- `call_subordinate.py` - Multi-agent delegation and communication
- `code_execution_tool.py` - Python/Node.js/Shell code execution
- `document_query.py` - Document analysis and Q&A
- `input.py` - Keyboard input simulation
- `memory_delete.py` - Memory deletion operations
- `memory_forget.py` - Memory forgetting operations
- `memory_load.py` - Memory retrieval operations
- `memory_save.py` - Memory storage operations
- `response.py` - Final response output (breaks message loop)
- `scheduler.py` - Task scheduling and cron-like functionality
- `search_engine.py` - Web search via SearXNG
- `unknown.py` - Fallback for undefined tools
- `vision_load.py` - Image processing and vision tasks

**Placeholder/Incomplete Tools** (`.py` files with underscores, not fully implemented):
- `browser_.py`, `browser_do_.py`, `browser_open_.py` - Browser tool variants
- `knowledge_tool_.py` - Knowledge base tool variant

**Prompt-Only Tools** (only `.md` prompts, no hardcoded Python):
- Referenced in `prompts/default/agent.system.tools.md` but implemented purely through prompts
- These tools use the `unknown.py` fallback handler and rely entirely on LLM reasoning

### Content and Configuration Directories

#### `prompts/` - Behavior Configuration
All agent behavior defined through markdown files:
- **`default/`**: Base prompt set
  - `agent.system.main.*.md` - Core agent behavior
  - `agent.system.tool.*.md` - Individual tool prompts (12 tools)
  - `fw.*.md` - Framework messages and responses
  - `memory.*.md` - Memory system prompts
  - `behaviour.*.md` - Behavior management prompts
- **Custom subdirectories**: User-created prompt overrides

#### `knowledge/` - Knowledge Base
- **`default/main/about/`**: Framework documentation (`github_readme.md`, `installation.md`)
- **`default/solutions/`**: Saved solution patterns
- **`custom/main/`**: User-uploaded knowledge files
- **`custom/solutions/`**: User-specific solutions

#### `instruments/` - Custom Scripts
- **`default/yt_download/`**: YouTube download example instrument
  - `yt_download.md` - Interface description
  - `yt_download.sh` - Shell script implementation
  - `download_video.py` - Python implementation
- **`custom/`**: User-created instruments

#### `memory/` - Persistent Memory
- Runtime-created directory for agent memory storage
- Vector database files and memory fragments
- Behavior rules storage (`behaviour.md`)

### Web Interface

#### `webui/` - Frontend Application
- **Root**: `index.html`, `index.css`, `index.js` - Main application
- **`js/`**: JavaScript modules (17 files)
  - Core: `api.js`, `components.js`, `messages.js`, `settings.js`
  - Features: `file_browser.js`, `scheduler.js`, `speech.js`, `tunnel.js`
  - External: `transformers@3.0.2.js` for local ML models
- **`css/`**: Stylesheets (9 files) - Modular styling for different components
- **`public/`**: SVG icons and assets (24 files) - All UI icons and branding
- **`components/`**: Reusable UI components
  - Message handling, settings panels, MCP integration interfaces

### Infrastructure

#### `docker/` - Containerization
- **`base/`**: Base image definition
  - `Dockerfile`, package installation scripts
  - SearXNG configuration files
- **`run/`**: Runtime container
  - `docker-compose.yml`, execution scripts
  - Nginx configuration, supervisor setup
  - Environment initialization and SSH setup

#### `docs/` - Documentation
- **Guides**: `installation.md`, `quickstart.md`, `usage.md`, `troubleshooting.md`
- **Architecture**: `architecture.md`, `contribution.md`
- **Specialized**: `mcp_setup.md`, `cuda_docker_setup.md`, `tunnel.md`
- **`res/`**: Images, diagrams, screenshots, and video resources
- **`designs/`**: Backend/frontend specification documents

### Runtime Directories
- **`logs/`**: HTML conversation logs (auto-generated)
- **`tmp/`**: Temporary files and cache
- **`work_dir/`**: User working directory (mounted in Docker)
- **`tests/`**: Test files and MCP server examples

## Tool Implementation Categories

### Hardcoded Python Tools (15 tools)
These tools have full Python implementations in `python/tools/` and corresponding prompt files:

1. **`behaviour_adjustment`** - Modifies agent behavior dynamically
2. **`browser_agent`** - Web browser automation using browser-use library
3. **`call_subordinate`** - Creates and communicates with subordinate agents
4. **`code_execution_tool`** - Executes Python, Node.js, and shell commands
5. **`document_query`** - Performs Q&A on documents using RAG
6. **`input`** - Simulates keyboard input for interactive applications
7. **`memory_delete`** - Deletes specific memories by ID
8. **`memory_forget`** - Removes memories by content/topic
9. **`memory_load`** - Retrieves memories based on query
10. **`memory_save`** - Stores information in persistent memory
11. **`response`** - Outputs final response (ends message loop)
12. **`scheduler`** - Manages scheduled tasks and cron-like operations
13. **`search_engine`** - Performs web search via SearXNG
14. **`unknown`** - Fallback handler for undefined tools
15. **`vision_load`** - Processes images and visual content

### Prompt-Only Tools (Variable)
These tools are defined purely through prompts in `prompts/default/agent.system.tool.*.md`:
- Handled by the `unknown.py` fallback mechanism
- Behavior defined entirely through LLM reasoning guided by prompts
- No hardcoded Python logic - rely on agent's ability to interpret and execute
- Examples visible in `agent.system.tools.md` include tools not in the hardcoded list above

### MCP Tools (Dynamic)
- External tools provided by MCP (Model Context Protocol) servers
- Dynamically loaded and available based on MCP server configuration
- Integrated through `python/helpers/mcp_handler.py`
- Can supplement or replace built-in tools

### Instruments (User-Extensible)
- Custom scripts in `instruments/custom/` directories
- Not technically "tools" but callable functions/procedures
- Stored in agent memory and recalled when needed
- Can be shell scripts, Python scripts, or other executables
- Don't consume system prompt tokens (unlike tools)