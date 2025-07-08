"""
Dedicated screenshot tool for on-demand screenshot capture
"""

from typing import Optional, Dict, Any, List
import logging
from pathlib import Path
import json

from python.helpers.tool import Tool, Response
from python.helpers.screenshots import (
    ScreenshotConfig,
    ScreenshotResult
)
from python.helpers.screenshots.utils.validation_utils import (
    validate_screenshot_config,
    sanitize_filename
)
from python.helpers.settings import get_settings

logger = logging.getLogger(__name__)

class ScreenshotTool(Tool):
    """
    Dedicated tool for on-demand screenshot capture
    
    This tool provides manual screenshot capture capabilities with extensive configuration options.
    It integrates with the browser agent's screenshot system to provide consistent functionality.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_initialized = False
        self.initialization_error = None
        self.dependencies_checked = False
        
        # Initialize screenshot system
        self._initialize_screenshot_system()
    
    def _initialize_screenshot_system(self) -> None:
        """Initialize screenshot system with validation and dependency checks."""
        try:
            # Check if Playwright is available
            self._check_playwright_availability()
            
            # Check screenshot directory structure
            self._check_screenshot_directories()
            
            # Validate screenshot utilities
            self._validate_screenshot_utilities()
            
            self.is_initialized = True
            from python.helpers.print_style import PrintStyle
            PrintStyle().success("Screenshot tool initialized successfully")
            
        except Exception as e:
            self.initialization_error = str(e)
            from python.helpers.print_style import PrintStyle
            PrintStyle().error(f"Screenshot tool initialization failed: {str(e)}")
            self.is_initialized = False
    
    def _check_playwright_availability(self) -> None:
        """Check if Playwright is available and functional."""
        try:
            # Try to import Playwright
            from playwright.async_api import Error as PlaywrightError
            logger.info("Playwright is available")
            
            # Try to check if browsers are installed (non-blocking)
            try:
                import subprocess
                result = subprocess.run(
                    ['python', '-m', 'playwright', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    logger.info(f"Playwright version: {result.stdout.strip()}")
                else:
                    logger.warning("Playwright command failed, but library is available")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning("Playwright browser check timed out or failed, but library is available")
                
        except ImportError:
            raise Exception("Playwright not installed. Run: pip install playwright && python -m playwright install")
        except Exception as e:
            raise Exception(f"Playwright availability check failed: {str(e)}")
    
    def _check_screenshot_directories(self) -> None:
        """Check and create screenshot directories if needed."""
        try:
            from python.helpers import files, persist_chat
            
            # Check if we can create screenshot directories
            if hasattr(self, 'agent') and self.agent and hasattr(self.agent, 'context'):
                base_path = files.get_abs_path(
                    persist_chat.get_chat_folder_path(self.agent.context.id),
                    "browser", "screenshots"
                )
                
                # Ensure directory exists
                if not files.make_dirs(base_path):
                    raise Exception(f"Cannot create screenshot directory: {base_path}")
                    
                # Test write permissions
                test_file = files.get_abs_path(base_path, "test_write.tmp")
                try:
                    with open(test_file, 'w') as f:
                        f.write('test')
                    files.remove(test_file)
                    logger.info(f"Screenshot directory validated: {base_path}")
                except Exception:
                    raise Exception(f"No write permissions in screenshot directory: {base_path}")
            else:
                logger.warning("Agent context not available, skipping directory check")
                    
        except Exception as e:
            raise Exception(f"Screenshot directory check failed: {str(e)}")
    
    def _validate_screenshot_utilities(self) -> None:
        """Validate screenshot utility functions are available."""
        try:
            # Check if screenshot utilities are importable
            from python.helpers.screenshots.utils.validation_utils import (
                validate_screenshot_config,
                sanitize_filename
            )
            from python.helpers.screenshots.utils.path_utils import (
                generate_screenshot_path,
                ensure_screenshot_directory
            )
            
            # Test basic functionality
            from python.helpers.screenshots import ScreenshotConfig
            test_config = ScreenshotConfig()
            
            # Test validation
            issues = validate_screenshot_config(test_config)
            if issues:
                logger.warning(f"Screenshot config validation issues: {issues}")
            else:
                logger.info("Screenshot config validation working")
                
            # Test filename sanitization
            test_filename = sanitize_filename("test_file.png")
            if not test_filename:
                raise Exception("Filename sanitization failed")
            
            logger.info("Screenshot utilities validated successfully")
                
        except ImportError as e:
            raise Exception(f"Screenshot utilities not available: {str(e)}")
        except Exception as e:
            raise Exception(f"Screenshot utilities validation failed: {str(e)}")
    
    async def execute(self, **kwargs) -> Response:
        """
        Execute screenshot capture with comprehensive parameter handling
        
        Supported parameters:
        - full_page: bool - Capture full page or just viewport
        - quality: int - JPEG quality (10-100)
        - format: str - Image format (png, jpeg, jpg)
        - timeout: int - Timeout in milliseconds
        - filename: str - Custom filename
        - force: bool - Force capture even if browser not active
        - metadata: dict - Additional metadata
        
        Returns:
            Response with screenshot information or error message
        """
        try:
            # Check if screenshot system is initialized
            if not self.is_initialized:
                error_msg = f"Screenshot tool not initialized: {self.initialization_error or 'Unknown error'}"
                logger.error(error_msg)
                return Response(message=error_msg, break_loop=False)
            
            # Get browser agent instance
            browser_agent = await self._get_browser_agent()
            if not browser_agent:
                return Response(
                    message="Screenshot tool requires an active browser session. Please start a browser session first using the browser_agent tool.",
                    break_loop=False
                )
            
            # Parse and validate parameters
            config_result = self._parse_screenshot_config(kwargs)
            if not config_result["valid"]:
                return Response(
                    message=f"Invalid screenshot configuration: {', '.join(config_result['errors'])}",
                    break_loop=False
                )
            
            config = config_result["config"]
            custom_filename = kwargs.get("filename")
            force = kwargs.get("force", False)
            metadata = kwargs.get("metadata", {})
            
            # Add tool metadata
            metadata.update({
                "tool": "screenshot_tool",
                "manual_request": True,
                "agent_id": self.agent.context.id,
                "requested_config": {
                    "full_page": config.full_page,
                    "quality": config.quality,
                    "format": config.format,
                    "timeout": config.timeout
                }
            })
            
            # Capture screenshot using browser agent's enhanced system
            if hasattr(browser_agent, 'manual_screenshot'):
                result = await browser_agent.manual_screenshot({
                    "full_page": config.full_page,
                    "quality": config.quality,
                    "format": config.format,
                    "timeout": config.timeout,
                    "filename": custom_filename,
                    "metadata": metadata
                })
            else:
                # Fallback for older browser agent
                result = await self._fallback_screenshot(browser_agent, config, custom_filename, metadata)
            
            # Format response
            if result.get("success"):
                return self._format_success_response(result)
            else:
                return self._format_error_response(result)
                
        except Exception as e:
            logger.error(f"Screenshot tool execution failed: {str(e)}")
            return Response(
                message=f"Screenshot tool failed: {str(e)}",
                break_loop=False
            )
    
    async def _get_browser_agent(self):
        """
        Get the browser agent instance from the current agent
        
        Returns:
            Browser agent instance or None if not available
        """
        try:
            # Check if browser agent is available in agent's tools
            if hasattr(self.agent, 'tools'):
                for tool in self.agent.tools:
                    if tool.__class__.__name__ == 'BrowserAgent':
                        return tool
            
            # Try to get from agent data
            browser_state = self.agent.get_data("_browser_agent_state")
            if browser_state:
                # Import here to avoid circular imports
                from python.tools.browser_agent import BrowserAgent
                browser_agent = BrowserAgent()
                browser_agent.agent = self.agent
                browser_agent.state = browser_state
                return browser_agent
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get browser agent: {str(e)}")
            return None
    
    def _parse_screenshot_config(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate screenshot configuration from kwargs
        
        Args:
            kwargs: Tool parameters
            
        Returns:
            Dictionary with validation results and parsed config
        """
        try:
            # Get current settings for defaults
            settings = get_settings()
            
            # Parse configuration parameters
            full_page = kwargs.get("full_page", False)
            quality = kwargs.get("quality", settings.get("screenshot_quality", 90))
            format_param = kwargs.get("format", settings.get("screenshot_format", "png"))
            timeout = kwargs.get("timeout", settings.get("screenshot_timeout", 3000))
            
            # Validate individual parameters
            errors = []
            
            # Validate full_page
            if not isinstance(full_page, bool):
                try:
                    full_page = str(full_page).lower() in ['true', '1', 'yes', 'on']
                except:
                    errors.append("full_page must be a boolean value")
            
            # Validate quality
            try:
                quality = int(quality)
                if quality < 10 or quality > 100:
                    errors.append("quality must be between 10 and 100")
            except (ValueError, TypeError):
                errors.append("quality must be an integer")
            
            # Validate format
            if format_param not in ["png", "jpeg", "jpg"]:
                errors.append("format must be 'png', 'jpeg', or 'jpg'")
            
            # Validate timeout
            try:
                timeout = int(timeout)
                if timeout < 1000 or timeout > 30000:
                    errors.append("timeout must be between 1000 and 30000 milliseconds")
            except (ValueError, TypeError):
                errors.append("timeout must be an integer")
            
            if errors:
                return {
                    "valid": False,
                    "errors": errors,
                    "config": None
                }
            
            # Create and validate configuration
            config = ScreenshotConfig(
                full_page=full_page,
                quality=quality,
                format=format_param,
                timeout=timeout
            )
            
            # Additional validation using utility function
            validation_issues = validate_screenshot_config(config)
            if validation_issues:
                return {
                    "valid": False,
                    "errors": validation_issues,
                    "config": None
                }
            
            return {
                "valid": True,
                "errors": [],
                "config": config
            }
            
        except Exception as e:
            logger.error(f"Failed to parse screenshot config: {str(e)}")
            return {
                "valid": False,
                "errors": [f"Configuration parsing error: {str(e)}"],
                "config": None
            }
    
    async def _fallback_screenshot(self, browser_agent, config: ScreenshotConfig, custom_filename: Optional[str], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback screenshot capture for older browser agents
        
        Args:
            browser_agent: Browser agent instance
            config: Screenshot configuration
            custom_filename: Optional custom filename
            metadata: Additional metadata
            
        Returns:
            Result dictionary
        """
        try:
            # Try to get page from browser agent
            if hasattr(browser_agent, 'state') and browser_agent.state:
                page = await browser_agent.state.get_page()
                if page:
                    # Use basic screenshot capture
                    from python.helpers import files, persist_chat
                    import uuid
                    import time
                    
                    # Generate filename
                    if custom_filename:
                        safe_filename = sanitize_filename(custom_filename)
                        if not safe_filename.endswith(f".{config.format}"):
                            safe_filename += f".{config.format}"
                    else:
                        safe_filename = f"screenshot_{uuid.uuid4()}.{config.format}"
                    
                    # Generate path
                    path = files.get_abs_path(
                        persist_chat.get_chat_folder_path(self.agent.context.id),
                        "browser", "screenshots",
                        safe_filename
                    )
                    
                    # Ensure directory exists
                    files.make_dirs(path)
                    
                    # Capture screenshot
                    await page.screenshot(
                        path=path,
                        full_page=config.full_page,
                        timeout=config.timeout
                    )
                    
                    return {
                        "success": True,
                        "path": path,
                        "screenshot": f"img://{path}&t={str(time.time())}",
                        "metadata": metadata
                    }
            
            return {
                "success": False,
                "error": "Browser page not available"
            }
            
        except Exception as e:
            logger.error(f"Fallback screenshot failed: {str(e)}")
            return {
                "success": False,
                "error": f"Fallback screenshot failed: {str(e)}"
            }
    
    def _format_success_response(self, result: Dict[str, Any]) -> Response:
        """
        Format successful screenshot response
        
        Args:
            result: Screenshot result
            
        Returns:
            Formatted response
        """
        path = result.get("path", "")
        metadata = result.get("metadata", {})
        
        # Create response message
        message_parts = [
            f"Screenshot captured successfully: {path}"
        ]
        
        # Add metadata information
        if metadata:
            config_info = metadata.get("requested_config", {})
            if config_info:
                message_parts.append(f"Configuration: {json.dumps(config_info, indent=2)}")
        
        # Add file information
        if path:
            try:
                file_path = Path(path)
                if file_path.exists():
                    file_size = file_path.stat().st_size
                    file_size_mb = round(file_size / (1024 * 1024), 2)
                    message_parts.append(f"File size: {file_size_mb} MB")
            except Exception as e:
                logger.warning(f"Failed to get file info: {str(e)}")
        
        message = "\n".join(message_parts)
        
        return Response(
            message=message,
            break_loop=False
        )
    
    def _format_error_response(self, result: Dict[str, Any]) -> Response:
        """
        Format error response
        
        Args:
            result: Screenshot result with error
            
        Returns:
            Formatted error response
        """
        error = result.get("error", "Unknown error")
        
        message = f"Screenshot capture failed: {error}"
        
        # Add troubleshooting suggestions
        suggestions = [
            "• Ensure browser session is active",
            "• Check screenshot configuration parameters",
            "• Verify sufficient disk space",
            "• Try with different timeout or quality settings"
        ]
        
        message += "\n\nTroubleshooting suggestions:\n" + "\n".join(suggestions)
        
        return Response(
            message=message,
            break_loop=False
        )
    
    def get_help(self) -> str:
        """
        Get help text for the screenshot tool
        
        Returns:
            Help text string
        """
        return """
Screenshot Tool - Capture browser screenshots manually

Usage:
  screenshot_tool(full_page=False, quality=90, format="png", timeout=3000, filename="custom.png")

Parameters:
  - full_page (bool): Capture full page or just viewport (default: False)
  - quality (int): JPEG quality 10-100 (default: 90, only for JPEG)
  - format (str): Image format - "png", "jpeg", "jpg" (default: "png")
  - timeout (int): Timeout in milliseconds (default: 3000)
  - filename (str): Custom filename (optional)
  - force (bool): Force capture even if conditions not met (default: False)
  - metadata (dict): Additional metadata to store (optional)

Examples:
  # Basic screenshot
  screenshot_tool()
  
  # Full page PNG
  screenshot_tool(full_page=True)
  
  # High quality JPEG
  screenshot_tool(format="jpeg", quality=95)
  
  # Custom filename with timeout
  screenshot_tool(filename="my_screenshot.png", timeout=5000)
  
  # With metadata
  screenshot_tool(metadata={"purpose": "debugging", "step": "login"})

Notes:
  - Requires active browser session
  - PNG format is lossless, JPEG is smaller but lossy
  - Full page screenshots may be large and slow
  - Screenshots are automatically cleaned up based on settings
"""

# Tool registration helper
def register_screenshot_tool():
    """
    Register the screenshot tool with the agent system
    This should be called during agent initialization
    """
    try:
        # This would be called by the agent system to register the tool
        # Implementation depends on the agent's tool registration mechanism
        pass
    except Exception as e:
        logger.error(f"Failed to register screenshot tool: {str(e)}")

# Export for tool system
__all__ = ['ScreenshotTool', 'register_screenshot_tool']