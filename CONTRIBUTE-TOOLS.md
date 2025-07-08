# CONTRIBUTE-TOOLS.md

## Agent Zero Tool Development Guide

This comprehensive guide provides detailed analysis of Agent Zero's tool architecture and best practices for developing robust, reliable, and modular tools that follow industry standards.

## Table of Contents

1. [Tool Architecture Overview](#tool-architecture-overview)
2. [Base Tool Class Analysis](#base-tool-class-analysis)
3. [Tool Implementation Patterns](#tool-implementation-patterns)
4. [Detailed Tool Analysis](#detailed-tool-analysis)
5. [Development Best Practices](#development-best-practices)
6. [Tool Integration Requirements](#tool-integration-requirements)
7. [How Tools Work in Agent Zero](#how-tools-work-in-agent-zero)
8. [Testing and Quality Assurance](#testing-and-quality-assurance)
9. [Advanced Patterns](#advanced-patterns)

## Tool Architecture Overview

### Core Components

Agent Zero's tool system is built around several key components:

1. **Base Tool Class** (`python/helpers/tool.py`) - Abstract base for all tools
2. **Response Class** - Standardized tool output format
3. **Agent Integration** - Deep integration with agent context and lifecycle
4. **Prompt System** - Markdown-based tool behavior definition
5. **Logging System** - Comprehensive logging and progress tracking

### Tool Lifecycle

```python
# Tool instantiation
tool = ToolClass(agent, name, method, args, message)

# Execution pipeline
await tool.before_execution(**kwargs)
response = await tool.execute(**kwargs)
await tool.after_execution(response, **kwargs)
```

## Base Tool Class Analysis

### Tool Class Structure

```python
@dataclass
class Response:
    message: str        # Tool output message
    break_loop: bool   # Whether to end agent message loop

class Tool:
    def __init__(self, agent: Agent, name: str, method: str | None, 
                 args: dict[str,str], message: str, **kwargs):
        self.agent = agent      # Agent instance
        self.name = name       # Tool name
        self.method = method   # Optional method/subcommand
        self.args = args       # Tool arguments
        self.message = message # Original agent message
```

### Core Methods

1. **`execute(**kwargs) -> Response`** (Abstract)
   - Primary tool logic implementation
   - Must return Response object
   - Should handle all tool-specific functionality

2. **`before_execution(**kwargs)`**
   - Pre-execution setup and logging
   - Argument validation and display
   - Progress initialization

3. **`after_execution(response: Response, **kwargs)`**
   - Post-execution cleanup and logging
   - History management
   - Result formatting and display

4. **`get_log_object()`**
   - Creates structured log entry
   - Customizable heading and metadata
   - Progress tracking support

### Key Attributes

- **`self.log`**: Log object for progress tracking
- **`self.agent`**: Full access to agent context and capabilities
- **`self.args`**: Parsed arguments from agent request
- **`self.method`**: Sub-method for tools with multiple operations

## Tool Implementation Patterns

### Pattern 1: Simple Single-Purpose Tools

**Example**: `ResponseTool` - Final response output

```python
class ResponseTool(Tool):
    async def execute(self, **kwargs):
        return Response(message=self.args["text"], break_loop=True)
    
    async def before_execution(self, **kwargs):
        pass  # No logging for response tool
    
    async def after_execution(self, response, **kwargs):
        pass  # No history addition for response tool
```

**Characteristics**:
- Minimal implementation
- Single responsibility
- Optional hook overrides
- Clear purpose (breaking message loop)

### Pattern 2: Method-Based Multi-Function Tools

**Example**: `SchedulerTool` - Multiple scheduler operations

```python
class SchedulerTool(Tool):
    async def execute(self, **kwargs):
        if self.method == "list_tasks":
            return await self.list_tasks(**kwargs)
        elif self.method == "create_scheduled_task":
            return await self.create_scheduled_task(**kwargs)
        # ... other methods
        else:
            return Response(message=f"Unknown method '{self.name}:{self.method}'", 
                          break_loop=False)
```

**Characteristics**:
- Method dispatch pattern
- Consistent error handling
- Modular sub-functionality
- JSON-based responses for structured data

### Pattern 3: State Management Tools

**Example**: `CodeExecution` - Persistent shell sessions

```python
class CodeExecution(Tool):
    async def execute(self, **kwargs):
        await self.prepare_state()  # Initialize/restore state
        
        runtime = self.args.get("runtime", "").lower().strip()
        session = int(self.args.get("session", 0))
        
        if runtime == "python":
            response = await self.execute_python_code(
                code=self.args["code"], session=session)
        # ... handle other runtimes
        
        return Response(message=response, break_loop=False)
    
    async def prepare_state(self, reset=False, session=None):
        self.state = self.agent.get_data("_cet_state")
        # State initialization and management
```

**Characteristics**:
- Persistent state across invocations
- Session management
- Resource cleanup
- Complex lifecycle management

### Pattern 4: External Integration Tools

**Example**: `BrowserAgent` - Browser automation

```python
class BrowserAgent(Tool):
    async def execute(self, message="", reset="", **kwargs):
        await self.prepare_state(reset=reset)
        task = self.state.start_task(message)
        
        # Wait for completion with timeout and progress updates
        while not task.is_ready():
            await self.agent.handle_intervention()
            update = await self.get_update()
            self.update_progress(update)
        
        result = await task.result()
        return Response(message=answer_text, break_loop=False)
```

**Characteristics**:
- Asynchronous task management
- Real-time progress updates
- External library integration
- Intervention handling
- Resource lifecycle management

### Pattern 5: Data Storage Tools

**Example**: `MemorySave`/`MemoryLoad` - Vector database operations

```python
class MemorySave(Tool):
    async def execute(self, text="", area="", **kwargs):
        if not area:
            area = Memory.Area.MAIN.value
        
        metadata = {"area": area, **kwargs}
        db = await Memory.get(self.agent)
        id = await db.insert_text(text, metadata)
        
        result = self.agent.read_prompt("fw.memory_saved.md", memory_id=id)
        return Response(message=result, break_loop=False)
```

**Characteristics**:
- Database abstraction layer
- Metadata handling
- Template-based responses
- Error handling for storage operations

## Detailed Tool Analysis

### Core Framework Tools

#### 1. ResponseTool (`response.py`)
- **Purpose**: Final response output that breaks the message loop
- **Pattern**: Simple single-purpose
- **Key Features**: 
  - Minimal implementation
  - Custom hooks to prevent logging
  - `break_loop=True` to end agent processing

#### 2. CodeExecution (`code_execution_tool.py`)
- **Purpose**: Execute Python, Node.js, and shell commands
- **Pattern**: State management with session persistence
- **Key Features**:
  - Multi-runtime support (Python/Node.js/Shell)
  - Session management for persistent environments
  - Real-time output streaming
  - Timeout handling with multiple strategies
  - Pattern recognition for shell prompts and dialogs
  - Connection retry logic for SSH sessions
  - Intervention support during execution

**State Management**:
```python
@dataclass
class State:
    shells: dict[int, LocalInteractiveSession | SSHInteractiveSession]
    docker: DockerContainerManager | None
```

**Execution Patterns**:
- **Python**: `ipython -c {escaped_code}`
- **Node.js**: `node /exe/node_eval.js {escaped_code}`
- **Terminal**: Direct shell command execution
- **Output**: Real-time streaming with timeout detection
- **Reset**: Per-session or full reset capability

#### 3. CallSubordinate (`call_subordinate.py`)
- **Purpose**: Multi-agent delegation and communication
- **Pattern**: Agent lifecycle management
- **Key Features**:
  - Subordinate agent creation and registration
  - Prompt profile switching
  - Superior-subordinate relationship management
  - Result forwarding without loop breaking

**Agent Hierarchy**:
```python
# Create subordinate
sub = Agent(self.agent.number + 1, self.agent.config, self.agent.context)
# Register relationships
sub.set_data(Agent.DATA_NAME_SUPERIOR, self.agent)
self.agent.set_data(Agent.DATA_NAME_SUBORDINATE, sub)
```

### Memory Management Tools

#### 4-7. Memory Tools (`memory_*.py`)
- **MemorySave**: Store text with metadata in vector database
- **MemoryLoad**: Retrieve memories using similarity search
- **MemoryDelete**: Remove memories by ID
- **MemoryForget**: Remove memories by content similarity

**Common Patterns**:
```python
db = await Memory.get(self.agent)  # Get agent's memory instance
# Operations use consistent thresholds and filters
docs = await db.search_similarity_threshold(
    query=query, limit=limit, threshold=threshold, filter=filter)
```

### External Service Tools

#### 8. SearchEngine (`search_engine.py`)
- **Purpose**: Web search via SearXNG
- **Pattern**: External API integration
- **Key Features**:
  - Intervention handling during search
  - Result formatting and limiting
  - Error handling for service failures

#### 9. BrowserAgent (`browser_agent.py`)
- **Purpose**: Web browser automation using browser-use library
- **Pattern**: Complex external integration with state management
- **Key Features**:
  - Browser session lifecycle management
  - Real-time screenshot capture
  - Task cancellation via intervention
  - Progress streaming with log updates
  - Timeout handling (5-minute default)
  - Browser profile customization

**Browser Configuration**:
```python
browser_session = browser_use.BrowserSession(
    browser_profile=browser_use.BrowserProfile(
        headless=True,
        disable_security=True,
        chromium_sandbox=False,
        screen={"width": 1024, "height": 2048},
        user_data_dir=f"agent_{self.agent.context.id}"
    )
)
```

### Specialized Tools

#### 10. BehaviourAdjustment (`behaviour_adjustment.py`)
- **Purpose**: Dynamic agent behavior modification
- **Pattern**: File-based persistence with LLM integration
- **Key Features**:
  - Rule merging using utility model
  - Persistent behavior storage
  - System prompt integration

#### 11. Scheduler (`scheduler.py`)
- **Purpose**: Task scheduling and management
- **Pattern**: Method-based multi-function
- **Key Features**:
  - Multiple task types (scheduled, ad-hoc, planned)
  - Cron expression validation
  - Task lifecycle management
  - Context isolation support

#### 12. Input (`input.py`)
- **Purpose**: Keyboard input simulation
- **Pattern**: Tool delegation
- **Key Features**:
  - Forwards to CodeExecution tool
  - Session-aware input handling
  - Simplified interface for terminal interaction

#### 13. DocumentQuery (`document_query.py`)
- **Purpose**: Document analysis and Q&A
- **Pattern**: Helper class delegation
- **Key Features**:
  - Multiple document format support
  - RAG-based question answering
  - Progress callback integration

#### 14. VisionLoad (`vision_load.py`)
- **Purpose**: Image processing and vision tasks
- **Pattern**: Async file processing with compression
- **Key Features**:
  - Image compression and optimization
  - Base64 encoding for LLM compatibility
  - Token estimation for context management
  - Custom history message format

#### 15. Unknown (`unknown.py`)
- **Purpose**: Fallback handler for undefined tools
- **Pattern**: Error handling with guidance
- **Key Features**:
  - Tool listing for user guidance
  - Consistent error messaging
  - System prompt integration

## Development Best Practices

### 1. Tool Design Principles

#### Single Responsibility
Each tool should have a clear, focused purpose:
```python
# Good: Focused on memory storage
class MemorySave(Tool):
    async def execute(self, text="", area="", **kwargs):
        # Only handles memory saving

# Bad: Mixed responsibilities
class MemoryAndSearch(Tool):
    async def execute(self, action="", **kwargs):
        if action == "save":
            # memory saving
        elif action == "search":
            # search logic
```

#### Consistent Interface
Follow established patterns for arguments and responses:
```python
# Consistent argument handling
class MyTool(Tool):
    async def execute(self, required_param="", optional_param="default", **kwargs):
        # Validate required parameters
        if not required_param:
            return Response(message="Required parameter missing", break_loop=False)
```

#### Error Handling
Implement comprehensive error handling:
```python
async def execute(self, **kwargs):
    try:
        # Tool logic
        result = await some_operation()
        return Response(message=result, break_loop=False)
    except SpecificException as e:
        # Handle specific errors
        return Response(message=f"Specific error: {e}", break_loop=False)
    except Exception as e:
        # Handle unexpected errors
        return Response(message=f"Unexpected error: {e}", break_loop=False)
```

### 2. State Management

#### Persistent State Pattern
```python
async def prepare_state(self, reset=False):
    self.state = self.agent.get_data("_tool_state_key")
    if not self.state or reset:
        self.state = initialize_state()
        self.agent.set_data("_tool_state_key", self.state)
```

#### Resource Cleanup
```python
class MyTool(Tool):
    def __del__(self):
        self.cleanup_resources()
    
    def cleanup_resources(self):
        if hasattr(self, 'connection'):
            self.connection.close()
```

### 3. Progress Tracking and Logging

#### Custom Log Objects
```python
def get_log_object(self):
    return self.agent.context.log.log(
        type="custom_type",
        heading=f"icon://custom_icon {self.agent.agent_name}: Tool Description",
        content="",
        kvps=self.args
    )
```

#### Progress Updates
```python
async def execute(self, **kwargs):
    total_steps = 5
    for i in range(total_steps):
        # Perform work
        await some_operation(i)
        
        # Update progress
        progress = f"Step {i+1}/{total_steps}: Description"
        self.log.update(progress=progress)
        self.agent.context.log.set_progress(progress)
```

### 4. Integration with Agent Context

#### Intervention Handling
```python
async def execute(self, **kwargs):
    # Check for user intervention
    await self.agent.handle_intervention()
    
    # Long-running operation with periodic checks
    for item in large_dataset:
        await process_item(item)
        await self.agent.handle_intervention()  # Allow user interruption
```

#### Utilizing Agent Capabilities
```python
async def execute(self, **kwargs):
    # Use agent's utility model
    result = await self.agent.call_utility_model(
        system="You are a helpful assistant",
        message="Process this data",
        callback=self.progress_callback
    )
    
    # Read agent prompts
    template = self.agent.read_prompt("custom_template.md", **kwargs)
    
    # Access agent memory
    db = await Memory.get(self.agent)
```

### 5. External Library Integration

#### Async Library Wrapping
```python
import asyncio
from external_lib import SyncLibrary

class ExternalTool(Tool):
    async def execute(self, **kwargs):
        # Wrap synchronous library
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, self.sync_operation, kwargs)
        return Response(message=result, break_loop=False)
    
    def sync_operation(self, kwargs):
        lib = SyncLibrary()
        return lib.process(kwargs)
```

#### Timeout Management
```python
async def execute(self, **kwargs):
    timeout_seconds = 30
    try:
        result = await asyncio.wait_for(
            self.long_running_operation(), 
            timeout=timeout_seconds
        )
        return Response(message=result, break_loop=False)
    except asyncio.TimeoutError:
        return Response(
            message=f"Operation timed out after {timeout_seconds} seconds", 
            break_loop=False
        )
```

## Tool Integration Requirements

### 1. File Structure

Create the following files for a new tool:

```
python/tools/my_tool.py                    # Tool implementation
prompts/default/agent.system.tool.my_tool.md  # Tool prompt/description
```

Update existing files:
```
prompts/default/agent.system.tools.md     # Add tool reference
```

### 2. Tool Implementation Template

```python
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle

class MyTool(Tool):
    
    async def execute(self, required_param="", optional_param="default", **kwargs):
        """
        Main tool execution logic.
        
        Args:
            required_param: Description of required parameter
            optional_param: Description with default value
            **kwargs: Additional arguments
            
        Returns:
            Response: Tool execution result
        """
        # Validate required parameters
        if not required_param:
            return Response(
                message="Error: required_param is mandatory", 
                break_loop=False
            )
        
        try:
            # Tool logic here
            result = await self.perform_operation(required_param, optional_param)
            
            return Response(message=result, break_loop=False)
            
        except Exception as e:
            error_msg = f"Tool execution failed: {str(e)}"
            PrintStyle().error(error_msg)
            return Response(message=error_msg, break_loop=False)
    
    async def perform_operation(self, param1, param2):
        """Tool-specific logic implementation."""
        # Implement your tool logic here
        return "Operation completed successfully"
    
    def get_log_object(self):
        """Custom log object for progress tracking."""
        return self.agent.context.log.log(
            type="custom_tool",
            heading=f"icon://settings {self.agent.agent_name}: Using My Tool",
            content="",
            kvps=self.args
        )
    
    async def before_execution(self, **kwargs):
        """Optional: Custom pre-execution logic."""
        await super().before_execution(**kwargs)
        # Add custom setup here
    
    async def after_execution(self, response: Response, **kwargs):
        """Optional: Custom post-execution logic."""
        await super().after_execution(response, **kwargs)
        # Add custom cleanup here
```

### 3. Prompt File Template

```markdown
<!-- prompts/default/agent.system.tool.my_tool.md -->

## Tool: my_tool

**Description**: Brief description of what the tool does.

**Usage**: 
```json
{
    "tool_name": "my_tool",
    "tool_args": {
        "required_param": "value",
        "optional_param": "optional_value"
    }
}
```

**Parameters**:
- `required_param` (required): Description of the required parameter
- `optional_param` (optional): Description of optional parameter, defaults to "default"

**Example**:
```json
{
    "tool_name": "my_tool", 
    "tool_args": {
        "required_param": "example_value",
        "optional_param": "custom_value"
    }
}
```

**Notes**: Any special usage notes or limitations.
```

### 4. Tools Registry Update

Add tool reference to `prompts/default/agent.system.tools.md`:

```markdown
{{ include './agent.system.tool.my_tool.md' }}
```

## How Tools Work in Agent Zero

### Tool Discovery and Automatic Loading

Agent Zero uses an automatic tool discovery system that requires no additional imports or manual registrations in the main codebase. The framework automatically discovers and loads tools based on a simple file naming convention and structure.

#### Discovery Process

1. **Python Implementation**: Tools are automatically discovered when a Python file exists in `python/tools/` with a class that inherits from the `Tool` base class
2. **Prompt Documentation**: Corresponding prompt files in `prompts/default/agent.system.tool.*.md` provide usage documentation and behavior guidance
3. **Registry Reference**: Tools are made available to agents when referenced in `prompts/default/agent.system.tools.md`

#### Tool Invocation

Agents invoke tools using the format:
```json
{
    "tool_name": "tool_name:method_name",
    "tool_args": {
        "parameter": "value"
    }
}
```

For single-purpose tools without methods:
```json
{
    "tool_name": "tool_name",
    "tool_args": {
        "parameter": "value"
    }
}
```

### Prompt File Patterns and Templates

#### Standard Prompt File Structure

All tool prompt files in `prompts/default/agent.system.tool.*.md` should follow this standardized structure:

```markdown
## Tool: tool_name

**Description**: Comprehensive description of what the tool does, its primary purpose, and key capabilities.

**Configuration**: (If applicable) Environment variables or configuration requirements.
- `ENV_VAR_NAME`: Description of required environment variable
- `OPTIONAL_VAR`: Description of optional configuration

**Methods Available**: (For multi-method tools)

### method_name
Brief description of what this method does.

**Usage**:
```json
{
    "tool_name": "tool_name:method_name",
    "tool_args": {
        "required_param": "value",
        "optional_param": "value"
    }
}
```

**Parameters**:
- `required_param` (required): Description of required parameter
- `optional_param` (optional): Description with default behavior

### (Repeat for each method)

**Response Format**: Description of what the tool returns (usually JSON).

**Error Handling**: Brief description of error handling approach.

**Examples**: 

Practical usage examples:
```json
{
    "tool_name": "tool_name:method_name",
    "tool_args": {
        "example_param": "example_value"
    }
}
```

**Security Notes**: (If applicable) Security considerations and best practices.

**Dependencies**: (If applicable) Required Python packages or external services.
```

#### Essential Prompt File Elements

1. **Tool Name Header**: Must match the filename pattern `## Tool: tool_name`
2. **JSON Usage Examples**: All examples must use valid JSON format with proper escaping
3. **Parameter Documentation**: Clear distinction between required and optional parameters
4. **Method Organization**: For multi-method tools, organize by method with clear subsections
5. **Response Format**: Specify what the tool returns (JSON, text, etc.)
6. **Error Handling**: Document error handling approach
7. **Examples Section**: Provide practical, copy-pasteable examples

#### Advanced Prompt Patterns

**Multi-Method Tools** (like email_manager, calendar_manager):
```markdown
**Methods Available**:

### method_one
Description of first method.

**Usage**:
```json
{
    "tool_name": "tool_name:method_one",
    "tool_args": {...}
}
```

### method_two
Description of second method.

**Usage**:
```json
{
    "tool_name": "tool_name:method_two", 
    "tool_args": {...}
}
```
```

**Configuration-Heavy Tools**:
```markdown
**Configuration**: Tool settings loaded from environment variables:
- `REQUIRED_CONFIG`: Required configuration item
- `OPTIONAL_CONFIG`: Optional configuration with default

**Setup Instructions**: 
1. Add required environment variables to .env file
2. Restart the agent framework
3. Tool will be automatically available
```

**External Service Integration**:
```markdown
**Dependencies**: This tool requires external services/packages:
- Service: Description and setup instructions
- Python package: Installation requirements

**Authentication**: How authentication/credentials are handled.
```

### Tools Registry Formatting (`prompts/default/agent.system.tools.md`)

#### Registry Structure

The `agent.system.tools.md` file serves as the master registry of all available tools. It uses a simple include pattern:

```markdown
## Tools available:

{{ include './agent.system.tool.response.md' }}

{{ include './agent.system.tool.call_sub.md' }}

{{ include './agent.system.tool.behaviour.md' }}

{{ include './agent.system.tool.search_engine.md' }}

{{ include './agent.system.tool.memory.md' }}

{{ include './agent.system.tool.code_exe.md' }}

{{ include './agent.system.tool.input.md' }}

{{ include './agent.system.tool.browser.md' }}

{{ include './agent.system.tool.scheduler.md' }}

{{ include './agent.system.tool.document_query.md' }}

{{ include './agent.system.tool.email_manager.md' }}

{{ include './agent.system.tool.calendar_manager.md' }}
```

#### Registry Requirements

1. **Include Pattern**: Each tool must be included using the exact pattern `{{ include './agent.system.tool.TOOLNAME.md' }}`
2. **File Naming**: The included filename must exactly match the tool's prompt file
3. **Order**: Tools can be listed in any order, but logical grouping is recommended
4. **No Additional Content**: The registry should only contain include statements and the header
5. **Blank Lines**: Include blank lines between tool includes for readability

#### Registry Update Process

When adding a new tool:

1. **Create Tool Files**: Implement both `python/tools/tool_name.py` and `prompts/default/agent.system.tool.tool_name.md`
2. **Add Registry Entry**: Add the include line to `agent.system.tools.md`
3. **Test Discovery**: Verify the tool appears in agent capabilities after restart

#### Common Registry Patterns

**Core Framework Tools** (typically listed first):
```markdown
{{ include './agent.system.tool.response.md' }}
{{ include './agent.system.tool.call_sub.md' }}
{{ include './agent.system.tool.behaviour.md' }}
```

**Utility Tools** (memory, search, execution):
```markdown
{{ include './agent.system.tool.memory.md' }}
{{ include './agent.system.tool.search_engine.md' }}
{{ include './agent.system.tool.code_exe.md' }}
```

**Integration Tools** (external services):
```markdown
{{ include './agent.system.tool.email_manager.md' }}
{{ include './agent.system.tool.calendar_manager.md' }}
{{ include './agent.system.tool.browser.md' }}
```

### Tool Integration Checklist

When implementing a new tool, ensure:

- [ ] **Python Implementation**: Tool class inherits from `Tool` and implements required methods
- [ ] **Prompt File**: Follows standard template with all required sections
- [ ] **Registry Update**: Tool is added to `agent.system.tools.md` with correct include pattern
- [ ] **Configuration**: Environment variables documented and handled properly
- [ ] **Error Handling**: Comprehensive error handling with descriptive messages
- [ ] **Documentation**: Complete examples and parameter documentation
- [ ] **Testing**: Tool behavior verified with various inputs
- [ ] **Dependencies**: External dependencies documented and installable

### Tool Naming Conventions

- **File Names**: Use snake_case (e.g., `calendar_manager.py`)
- **Class Names**: Use PascalCase matching filename (e.g., `CalendarManager`)
- **Tool Names**: Use snake_case matching filename (e.g., `calendar_manager`)
- **Method Names**: Use snake_case with descriptive verbs (e.g., `create_event`, `list_calendars`)
- **Prompt Files**: Match Python filename exactly (e.g., `agent.system.tool.calendar_manager.md`)

## Testing and Quality Assurance

### 1. Unit Testing Pattern

```python
import pytest
from unittest.mock import Mock, AsyncMock
from python.tools.my_tool import MyTool

class TestMyTool:
    
    @pytest.fixture
    def mock_agent(self):
        agent = Mock()
        agent.context = Mock()
        agent.context.log = Mock()
        agent.context.log.log = Mock()
        return agent
    
    @pytest.fixture
    def tool(self, mock_agent):
        return MyTool(
            agent=mock_agent,
            name="my_tool",
            method=None,
            args={"required_param": "test_value"},
            message="test message"
        )
    
    @pytest.mark.asyncio
    async def test_execute_success(self, tool):
        response = await tool.execute(required_param="test_value")
        
        assert response.break_loop == False
        assert "success" in response.message.lower()
    
    @pytest.mark.asyncio
    async def test_execute_missing_param(self, tool):
        response = await tool.execute()
        
        assert response.break_loop == False
        assert "error" in response.message.lower()
```

### 2. Integration Testing

```python
@pytest.mark.integration
async def test_tool_integration(agent_context):
    """Test tool integration with real agent context."""
    tool = MyTool(
        agent=agent_context.agent0,
        name="my_tool", 
        method=None,
        args={"required_param": "integration_test"},
        message="integration test"
    )
    
    response = await tool.execute()
    assert response.message
    assert response.break_loop in [True, False]
```

### 3. Error Handling Tests

```python
@pytest.mark.asyncio
async def test_error_handling(tool, monkeypatch):
    """Test tool behavior under error conditions."""
    
    # Mock external dependency to raise exception
    async def mock_failing_operation(*args, **kwargs):
        raise Exception("Simulated failure")
    
    monkeypatch.setattr(tool, "perform_operation", mock_failing_operation)
    
    response = await tool.execute(required_param="test")
    assert "failed" in response.message.lower()
    assert response.break_loop == False
```

## Advanced Patterns

### 1. Streaming and Real-time Updates

```python
class StreamingTool(Tool):
    async def execute(self, **kwargs):
        async def progress_callback(chunk: str, full: str):
            # Update progress in real-time
            self.log.update(progress=full)
            self.agent.context.log.set_progress(f"Processing: {len(full)} chars")
        
        result = await self.streaming_operation(progress_callback)
        return Response(message=result, break_loop=False)
```

### 2. Multi-step Operations with Checkpoints

```python
class ComplexTool(Tool):
    async def execute(self, **kwargs):
        steps = [
            ("Initialize", self.step_initialize),
            ("Process", self.step_process), 
            ("Finalize", self.step_finalize)
        ]
        
        results = []
        for i, (name, step_func) in enumerate(steps):
            self.log.update(progress=f"Step {i+1}/{len(steps)}: {name}")
            
            try:
                result = await step_func(**kwargs)
                results.append(f"{name}: {result}")
                
                # Checkpoint for intervention
                await self.agent.handle_intervention()
                
            except Exception as e:
                return Response(
                    message=f"Failed at step '{name}': {e}", 
                    break_loop=False
                )
        
        return Response(message="\n".join(results), break_loop=False)
```

### 3. Tool Composition and Delegation

```python
class CompositeTool(Tool):
    async def execute(self, **kwargs):
        # Use another tool as part of this tool's operation
        from python.tools.code_execution_tool import CodeExecution
        
        # Delegate to code execution tool
        code_tool = CodeExecution(
            agent=self.agent,
            name="code_execution_tool",
            method="",
            args={"runtime": "python", "code": "print('Hello from composite tool')"},
            message=self.message
        )
        
        code_response = await code_tool.execute()
        
        # Process the result and add our own logic
        enhanced_result = f"Composite result: {code_response.message}"
        
        return Response(message=enhanced_result, break_loop=False)
```

### 4. Configuration-Driven Tools

```python
class ConfigurableTool(Tool):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = self.load_config()
    
    def load_config(self):
        """Load tool-specific configuration."""
        config_path = f"config/{self.name}.json"
        if files.exists(config_path):
            return json.loads(files.read_file(config_path))
        return self.default_config()
    
    def default_config(self):
        return {
            "timeout": 30,
            "retry_count": 3,
            "batch_size": 10
        }
    
    async def execute(self, **kwargs):
        timeout = self.config.get("timeout", 30)
        retry_count = self.config.get("retry_count", 3)
        
        for attempt in range(retry_count):
            try:
                result = await asyncio.wait_for(
                    self.perform_operation(**kwargs),
                    timeout=timeout
                )
                return Response(message=result, break_loop=False)
            except asyncio.TimeoutError:
                if attempt == retry_count - 1:
                    return Response(
                        message=f"Operation failed after {retry_count} attempts",
                        break_loop=False
                    )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 5. Tool Analytics and Metrics

```python
class AnalyticsTool(Tool):
    async def before_execution(self, **kwargs):
        await super().before_execution(**kwargs)
        self.start_time = time.time()
        self.metrics = {
            "tool_name": self.name,
            "agent_id": self.agent.context.id,
            "start_time": self.start_time
        }
    
    async def after_execution(self, response: Response, **kwargs):
        await super().after_execution(response, **kwargs)
        
        # Record metrics
        self.metrics.update({
            "duration": time.time() - self.start_time,
            "success": "error" not in response.message.lower(),
            "response_length": len(response.message)
        })
        
        # Store metrics for analysis
        await self.store_metrics(self.metrics)
    
    async def store_metrics(self, metrics):
        """Store tool usage metrics."""
        metrics_file = "logs/tool_metrics.jsonl"
        with open(metrics_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")
```

This comprehensive guide provides the foundation for developing high-quality tools for Agent Zero. Follow these patterns and best practices to create tools that are robust, maintainable, and integrate seamlessly with the Agent Zero ecosystem.