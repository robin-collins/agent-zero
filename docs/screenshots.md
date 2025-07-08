# Screenshot System Documentation

## Overview

The Agent Zero screenshot system provides comprehensive screenshot capture capabilities for browser sessions. It follows SOLID principles with a modular architecture that supports multiple providers, automatic cleanup, and intelligent capture triggers.

## Architecture

### Core Components

1. **Screenshot Provider Interface**: Abstract base class for screenshot providers
2. **Playwright Provider**: Concrete implementation using Playwright
3. **Browser Screenshot Manager**: Manages screenshot capture and storage
4. **Auto Screenshot Manager**: Handles automatic trigger-based captures
5. **Validation Utilities**: Input validation and sanitization
6. **Cleanup Utilities**: Automatic file management and cleanup

### Design Principles

- **Single Responsibility**: Each component has a focused purpose
- **Open/Closed**: Extensible through provider interfaces
- **Liskov Substitution**: Providers are interchangeable
- **Interface Segregation**: Clean, focused interfaces
- **Dependency Inversion**: Depends on abstractions, not concrete implementations

## Features

### Automatic Screenshot Capture

- **Navigation Triggers**: Capture screenshots when navigating to new pages
- **Interaction Triggers**: Capture after user interactions (clicks, form submissions)
- **Error Triggers**: High-quality captures when errors occur
- **Timeout Triggers**: Capture on operation timeouts

### Manual Screenshot Capture

- **Screenshot Tool**: Dedicated tool for on-demand captures
- **Configuration Options**: Quality, format, timeout, dimensions
- **Custom Filenames**: User-defined naming
- **Metadata Support**: Rich metadata storage

### File Management

- **Automatic Cleanup**: Remove old screenshots based on age and count
- **Storage Optimization**: Configurable retention policies
- **Metadata Storage**: Detailed information about each screenshot
- **Format Support**: PNG (lossless) and JPEG (compressed)

### Error Handling

- **Graceful Degradation**: Continue operation if screenshots fail
- **Comprehensive Logging**: Detailed error reporting
- **Retry Logic**: Automatic retry for transient failures
- **Validation**: Input validation and sanitization

## Configuration

### Settings

Screenshot behavior is controlled through the settings system:

```json
{
  "auto_screenshot": true,
  "screenshot_quality": 90,
  "screenshot_format": "png",
  "screenshot_timeout": 3000,
  "screenshot_cleanup_hours": 24,
  "max_screenshot_files": 1000,
  "screenshot_trigger_navigation": true,
  "screenshot_trigger_interaction": true,
  "screenshot_trigger_error": true,
  "screenshot_create_metadata": true
}
```

### Format Options

- **PNG**: Lossless compression, best for UI screenshots
- **JPEG**: Lossy compression, smaller files, good for photos

### Quality Settings

- **Range**: 10-100 (JPEG only)
- **Recommended**: 90 for general use, 95 for high quality
- **Impact**: Higher quality = larger files

### Timeout Settings

- **Range**: 1000-30000 milliseconds
- **Default**: 3000ms (3 seconds)
- **Usage**: Increase for complex pages, decrease for faster capture

## Usage

### Browser Agent Integration

The screenshot system is automatically integrated with the browser agent:

```python
# Screenshots are captured automatically during browser sessions
browser_agent.execute("Navigate to https://example.com")
# -> Automatic navigation screenshot

# Manual screenshot capture
result = await browser_agent.manual_screenshot({
    "full_page": True,
    "quality": 95,
    "format": "png"
})
```

### Screenshot Tool

Use the dedicated screenshot tool for manual captures:

```python
# Basic screenshot
screenshot_tool()

# Full page with custom settings
screenshot_tool(full_page=True, quality=95, format="jpeg")

# With custom filename and metadata
screenshot_tool(
    filename="login_page.png",
    metadata={"step": "authentication", "user": "test"}
)
```

### Programmatic Usage

Direct usage of the screenshot system:

```python
from python.helpers.screenshots import (
    PlaywrightScreenshotProvider,
    BrowserScreenshotManager,
    ScreenshotConfig
)

# Create provider
provider = PlaywrightScreenshotProvider(page)

# Create manager
manager = BrowserScreenshotManager(
    provider=provider,
    base_path=Path("/path/to/screenshots"),
    max_age_hours=24,
    max_files=1000
)

# Initialize and capture
await manager.initialize()
config = ScreenshotConfig(full_page=True, quality=90)
result = await manager.capture_screenshot(config)
```

## Storage

### File Organization

```
<chat_folder>/
├── browser/
│   └── screenshots/
│       ├── screenshot_1234567890_abcd1234.png
│       ├── screenshot_1234567891_efgh5678.png
│       └── .metadata/
│           ├── screenshot_1234567890_abcd1234.json
│           └── screenshot_1234567891_efgh5678.json
```

### Metadata Format

```json
{
  "stored_at": 1234567890.123,
  "original_path": "/path/to/screenshot.png",
  "identifier": "screenshot_1234567890_abcd1234",
  "file_size": 145678,
  "format": "png",
  "full_page": false,
  "quality": 90,
  "capture_time_ms": 1234,
  "page_info": {
    "url": "https://example.com",
    "title": "Example Page",
    "viewport": {"width": 1280, "height": 720}
  },
  "provider": "playwright",
  "trigger_type": "navigation",
  "auto_capture": true,
  "agent_id": "agent_123",
  "metadata": {
    "custom": "data"
  }
}
```

## API Reference

### ScreenshotConfig

Configuration object for screenshot capture:

```python
@dataclass
class ScreenshotConfig:
    full_page: bool = False          # Capture full page vs viewport
    timeout: int = 3000              # Timeout in milliseconds
    quality: int = 90                # JPEG quality (10-100)
    format: str = "png"              # Format: "png", "jpeg", "jpg"
    width: Optional[int] = None      # Custom width
    height: Optional[int] = None     # Custom height
```

### ScreenshotResult

Result object from screenshot capture:

```python
@dataclass
class ScreenshotResult:
    success: bool                    # Whether capture succeeded
    path: Optional[Path] = None      # Path to screenshot file
    error: Optional[str] = None      # Error message if failed
    metadata: Optional[Dict] = None  # Additional metadata
    timestamp: Optional[float] = None # Capture timestamp
```

### BrowserScreenshotManager

Main manager class:

```python
class BrowserScreenshotManager:
    async def initialize() -> bool
    async def capture_screenshot(
        config: Optional[ScreenshotConfig] = None,
        custom_filename: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> ScreenshotResult
    async def capture_with_metadata(
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]
    async def get_statistics() -> Dict[str, Any]
    async def manual_cleanup(dry_run: bool = False) -> Dict[str, Any]
    async def cleanup() -> None
```

### AutoScreenshotManager

Automatic capture manager:

```python
class AutoScreenshotManager:
    async def trigger_screenshot(
        trigger_type: TriggerType,
        context: Optional[Dict] = None,
        force: bool = False
    ) -> Optional[ScreenshotResult]
    async def on_navigation(url: str, context: Optional[Dict] = None)
    async def on_error(error: str, context: Optional[Dict] = None)
    async def on_interaction(action: str, context: Optional[Dict] = None)
    def enable_trigger(trigger_type: TriggerType, enabled: bool = True)
    def configure_trigger(
        trigger_type: TriggerType,
        config: Optional[ScreenshotConfig] = None,
        condition: Optional[Callable] = None,
        metadata: Optional[Dict] = None
    )
```

## Migration Guide

### From Original System

The enhanced screenshot system is designed to be backward compatible:

1. **Automatic Migration**: Enhanced browser agent maintains compatibility
2. **Gradual Adoption**: Can be enabled incrementally
3. **Fallback Support**: Falls back to original system if needed

### Migration Steps

1. **Install Enhanced System**: Deploy new screenshot modules
2. **Update Configuration**: Add new settings to configuration
3. **Test Integration**: Verify screenshot capture works
4. **Enable Features**: Gradually enable new features
5. **Monitor Performance**: Check for any issues

### Rollback Procedure

If issues occur, rollback is supported:

```python
# Rollback to original browser agent
from python.tools.migrate_browser_agent import rollback_browser_agent
rollback_browser_agent()
```

## Troubleshooting

### Common Issues

1. **Screenshots Not Captured**
   - Check browser session is active
   - Verify provider is available
   - Check timeout settings

2. **Large File Sizes**
   - Reduce JPEG quality
   - Use viewport instead of full page
   - Consider PNG vs JPEG format

3. **Slow Capture**
   - Reduce timeout values
   - Use viewport screenshots
   - Check page complexity

4. **Disk Space Issues**
   - Reduce cleanup hours
   - Lower max file count
   - Check cleanup is running

### Debug Information

Enable debug logging:

```python
import logging
logging.getLogger("python.helpers.screenshots").setLevel(logging.DEBUG)
```

Get system statistics:

```python
stats = await browser_manager.get_statistics()
print(json.dumps(stats, indent=2))
```

### Performance Optimization

1. **Configuration Tuning**
   - Adjust timeout values
   - Optimize quality settings
   - Use appropriate formats

2. **Cleanup Management**
   - Regular cleanup scheduling
   - Appropriate retention policies
   - Monitor disk usage

3. **Resource Management**
   - Proper cleanup on shutdown
   - Memory-efficient operations
   - Concurrent capture limits

## Security Considerations

### Path Validation

- All file paths are validated and sanitized
- Directory traversal protection
- Safe filename generation

### Resource Limits

- Maximum file sizes enforced
- Timeout limits prevent hanging
- Memory usage controls

### Access Control

- Screenshots stored in session directories
- Proper file permissions
- Secure cleanup procedures

## Testing

### Unit Tests

Run the test suite:

```bash
cd /mnt/d/a0/agent-zero
python -m pytest tests/screenshots/ -v
```

### Integration Tests

Test with real browser:

```python
# Run integration test
python tests/screenshots/test_integration.py
```

### Performance Tests

Benchmark screenshot capture:

```python
# Run performance tests
python tests/screenshots/test_performance.py
```

## Contributing

### Adding New Providers

1. Implement `ScreenshotProvider` interface
2. Add provider to registry
3. Create unit tests
4. Update documentation

### Extending Functionality

1. Follow SOLID principles
2. Add comprehensive tests
3. Update documentation
4. Consider backward compatibility

### Code Standards

- Type hints required
- Comprehensive error handling
- Logging for debugging
- Clean code principles

## Future Enhancements

### Planned Features

1. **Cloud Storage**: Support for cloud storage providers
2. **Compression**: Automatic compression of old screenshots
3. **Annotations**: Support for screenshot annotations
4. **Analytics**: Usage analytics and reporting
5. **Batch Operations**: Bulk screenshot operations

### Extension Points

- New storage providers
- Additional image formats
- Custom trigger types
- Advanced cleanup strategies
- Integration with other tools

## License

This screenshot system is part of Agent Zero and follows the same license terms.