# CHANGELOG

## [Unreleased]

### Added
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