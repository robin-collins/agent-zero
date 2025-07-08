# CHANGELOG

## [Unreleased]

### Added
- **Enhanced Screenshot System**: Complete rewrite of screenshot functionality with modular architecture
  - **Architecture**: Modular design following SOLID principles with pluggable providers
  - **Error Handling**: Comprehensive error handling and graceful degradation
  - **Automatic Capture**: Intelligent triggers for navigation, interaction, and error events
  - **Manual Capture**: Dedicated screenshot tool with extensive configuration options
  - **Resource Management**: Automatic cleanup, file management, and storage optimization
  - **Settings Integration**: Comprehensive validation and configuration system
  - **Quality Assurance**: Full test coverage, validation scripts, and documentation
  - **Core Components Added**:
    - `python/helpers/screenshots/` - Complete screenshot module with interfaces, providers, managers, utilities, and storage
    - `python/helpers/screenshots/interfaces/screenshot_provider.py` - Abstract provider interface
    - `python/helpers/screenshots/providers/playwright_provider.py` - Playwright implementation
    - `python/helpers/screenshots/managers/browser_screenshot_manager.py` - Main screenshot manager
    - `python/helpers/screenshots/managers/auto_screenshot_manager.py` - Automatic trigger manager
    - `python/helpers/screenshots/utils/path_utils.py` - Path management utilities
    - `python/helpers/screenshots/utils/cleanup_utils.py` - Cleanup and maintenance utilities
    - `python/helpers/screenshots/utils/validation_utils.py` - Validation and sanitization
    - `python/helpers/screenshots/storage/file_storage.py` - File system storage provider
  - **Tools and Integration**:
    - `python/tools/screenshot_tool.py` - Dedicated screenshot capture tool
    - `python/tools/browser_agent_enhanced.py` - Enhanced browser agent with screenshot integration
    - `python/tools/migrate_browser_agent.py` - Migration utility for browser agent
    - `python/helpers/settings_screenshot_integration.py` - Settings system integration
    - `prompts/default/agent.system.tool.screenshot.md` - Screenshot tool prompts and documentation
  - **Documentation and Testing**:
    - `docs/screenshots.md` - Comprehensive system documentation with API reference
    - `tests/screenshots/test_screenshot_provider.py` - Provider unit tests
    - `tests/screenshots/test_screenshot_manager.py` - Manager integration tests
    - `deploy_screenshot_system.py` - Automated deployment script with validation
    - `validate_screenshot_implementation.py` - Implementation validation and verification
  - **Enhanced Features**:
    - Support for PNG (lossless) and JPEG (compressed) formats
    - Configurable quality settings and timeout controls
    - Automatic file cleanup based on age and count limits
    - Metadata storage with comprehensive screenshot information
    - Duplicate detection and intelligent capture spacing
    - Full error recovery and fallback mechanisms
    - Backward compatibility with existing browser agent
    - Security features including path validation and sanitization

- **GitHub Actions Workflow**: Added container image build workflow for GHCR (GitHub Container Registry)
  - Manual trigger workflow for building base and main container images
  - Multi-platform support (linux/amd64, linux/arm64)
  - Configurable branch selection for builds
  - Proper dependency handling between base and main image builds
  - GitHub Actions caching for improved build performance
  - File added: `.github/workflows/build-containers.yml`
- **Calendar Manager Tool**: New CalDAV protocol integration tool for comprehensive calendar management
  - Support for listing calendars and events
  - Create, read, update, and delete calendar events
  - Event search functionality with text queries
  - Full timezone support with pytz integration
  - Multi-calendar support
  - All-day event handling
  - Robust error handling and connection management
  - Files added:
    - `python/tools/calendar_manager.py` - Tool implementation
    - `prompts/default/agent.system.tool.calendar_manager.md` - Tool documentation and prompts
  - Updated `prompts/default/agent.system.tools.md` to include new tool
- **Enhanced Documentation**: Major updates to `CONTRIBUTE-TOOLS.md` with comprehensive tool integration guide
  - Added "How Tools Work in Agent Zero" section explaining automatic tool discovery
  - Documented prompt file patterns and templates with examples
  - Added tools registry formatting requirements and best practices
  - Included tool integration checklist and naming conventions
  - Enhanced with real-world examples from calendar_manager and email_manager tools
- **Enhanced Email Manager Tool**: Updated both implementation and documentation
  - **New Feature**: Added HTML email format support alongside existing plain text
  - **Implementation**: Enhanced `python/tools/email_manager.py` with format parameter for send_email method
  - **Documentation**: Updated `prompts/default/agent.system.tool.email_manager.md`
    - Added "Important" guidelines section for proper email handling
    - Updated JSON examples to include "thoughts" and "headline" fields for Agent Zero compatibility
    - Added comprehensive configuration documentation with optional variables
    - Enhanced examples with practical scenarios including HTML email examples
    - Documented new format parameter with plain text and HTML options

### Changed

### Fixed
- **Code Quality**: Fixed ruff linter errors in email manager tool
  - Replaced bare `except:` clauses with `except Exception:` for better error handling
  - Both email_manager.py and calendar_manager.py now pass all linting checks

### Removed

---

*Note: This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.*