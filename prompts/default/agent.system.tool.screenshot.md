# Screenshot Tool

The screenshot tool allows you to capture screenshots manually from the current browser session.

## Usage

Use the `screenshot_tool` to capture screenshots with various configuration options.

## Parameters

- **full_page** (bool, optional): Capture full page or just viewport
  - `true`: Capture entire page including scrollable content
  - `false`: Capture only visible viewport (default, faster)

- **quality** (int, optional): JPEG quality from 10 to 100
  - Higher values = better quality but larger files
  - Only applies to JPEG format
  - Default: 90

- **format** (str, optional): Image format
  - `"png"`: Lossless compression, best for text/UI (default)
  - `"jpeg"` or `"jpg"`: Lossy compression, smaller files

- **timeout** (int, optional): Timeout in milliseconds
  - Range: 1000-30000 ms
  - Default: 3000 ms (3 seconds)

- **filename** (str, optional): Custom filename
  - Will be sanitized for filesystem safety
  - Extension will be added if missing

- **metadata** (dict, optional): Additional metadata to store
  - Useful for organizing screenshots

## Examples

### Basic screenshot
```
screenshot_tool()
```

### Full page screenshot
```
screenshot_tool(full_page=true)
```

### High quality JPEG
```
screenshot_tool(format="jpeg", quality=95)
```

### Custom filename
```
screenshot_tool(filename="login_page.png")
```

### With metadata
```
screenshot_tool(metadata={"step": "after_login", "purpose": "verification"})
```

## Requirements

- An active browser session must be running
- Use `browser_agent` first to start a browser session

## Response

The tool returns success/failure status and the screenshot file path if successful.

## Error Handling

Common errors:
- No active browser session
- Invalid configuration parameters
- Insufficient disk space
- Page loading timeout

## Best Practices

1. Use PNG for screenshots with text or UI elements
2. Use JPEG for screenshots with mostly images/photos
3. Use viewport screenshots for faster capture
4. Use full page screenshots for comprehensive documentation
5. Set appropriate timeouts for complex pages
6. Include descriptive metadata for organization

## Storage

Screenshots are automatically:
- Saved to the chat's screenshot directory
- Cleaned up after configured time period
- Included in backup operations
- Indexed with metadata if enabled

## Integration

The screenshot tool integrates with:
- Browser agent's enhanced screenshot system
- Automatic cleanup utilities
- Settings configuration
- Metadata storage system