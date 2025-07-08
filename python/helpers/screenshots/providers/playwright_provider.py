"""
Playwright-based screenshot provider implementation
"""

from typing import Optional, Dict, Any
from pathlib import Path
import asyncio
import logging
import time
from playwright.async_api import Page, Error as PlaywrightError

from ..interfaces.screenshot_provider import (
    ScreenshotProvider, 
    ScreenshotConfig, 
    ScreenshotResult,
    ScreenshotTimeoutError,
    ScreenshotUnavailableError,
    ScreenshotConfigurationError
)

logger = logging.getLogger(__name__)

class PlaywrightScreenshotProvider(ScreenshotProvider):
    """Playwright-based screenshot provider with comprehensive error handling"""
    
    def __init__(self, page: Page):
        if not page:
            raise ValueError("Page instance cannot be None")
        
        self.page = page
        self._is_available = True
        self._capabilities = {
            "formats": ["png", "jpeg", "jpg"],
            "full_page": True,
            "viewport_clipping": True,
            "quality_control": True,
            "timeout_control": True,
            "max_timeout": 30000,
            "max_width": 10000,
            "max_height": 10000
        }
    
    async def capture_screenshot(
        self, 
        config: ScreenshotConfig,
        output_path: Path
    ) -> ScreenshotResult:
        """Capture screenshot using Playwright with comprehensive error handling"""
        start_time = time.time()
        
        try:
            # Validate configuration
            await self._validate_config(config)
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if provider is available
            if not await self.is_available():
                raise ScreenshotUnavailableError("Playwright provider is not available")
            
            # Prepare screenshot options
            screenshot_options = self._prepare_screenshot_options(config, output_path)
            
            # Capture screenshot with timeout handling
            try:
                await asyncio.wait_for(
                    self.page.screenshot(**screenshot_options),
                    timeout=config.timeout / 1000.0
                )
            except asyncio.TimeoutError:
                raise ScreenshotTimeoutError(f"Screenshot timeout after {config.timeout}ms")
            
            # Verify file was created and get metadata
            if not output_path.exists():
                raise ScreenshotUnavailableError("Screenshot file was not created")
            
            metadata = await self._get_file_metadata(output_path, config, start_time)
            
            logger.info(f"Screenshot captured successfully: {output_path}")
            
            return ScreenshotResult(
                success=True,
                path=output_path,
                metadata=metadata,
                timestamp=time.time()
            )
            
        except ScreenshotTimeoutError as e:
            logger.error(f"Screenshot timeout: {str(e)}")
            return ScreenshotResult(
                success=False,
                error=str(e),
                timestamp=time.time()
            )
        except ScreenshotUnavailableError as e:
            logger.error(f"Screenshot unavailable: {str(e)}")
            return ScreenshotResult(
                success=False,
                error=str(e),
                timestamp=time.time()
            )
        except PlaywrightError as e:
            logger.error(f"Playwright error: {str(e)}")
            return ScreenshotResult(
                success=False,
                error=f"Playwright error: {str(e)}",
                timestamp=time.time()
            )
        except Exception as e:
            logger.error(f"Unexpected screenshot error: {str(e)}")
            return ScreenshotResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                timestamp=time.time()
            )
    
    async def is_available(self) -> bool:
        """Check if Playwright page is available and connected"""
        try:
            if not self.page or not self._is_available:
                return False
            
            # Check if page is still connected by evaluating a simple expression
            await self.page.evaluate("1 + 1")
            return True
            
        except Exception as e:
            logger.warning(f"Playwright provider unavailable: {str(e)}")
            self._is_available = False
            return False
    
    async def cleanup(self) -> None:
        """Clean up Playwright resources"""
        logger.info("Cleaning up Playwright screenshot provider")
        self._is_available = False
        # Note: Page cleanup is handled by the browser agent
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """Get provider capabilities"""
        return self._capabilities.copy()
    
    async def _validate_config(self, config: ScreenshotConfig) -> None:
        """Validate screenshot configuration against provider capabilities"""
        if config.format not in self._capabilities["formats"]:
            raise ScreenshotConfigurationError(
                f"Format '{config.format}' not supported. Supported formats: {self._capabilities['formats']}"
            )
        
        if config.timeout > self._capabilities["max_timeout"]:
            raise ScreenshotConfigurationError(
                f"Timeout {config.timeout}ms exceeds maximum {self._capabilities['max_timeout']}ms"
            )
        
        if config.width and config.width > self._capabilities["max_width"]:
            raise ScreenshotConfigurationError(
                f"Width {config.width}px exceeds maximum {self._capabilities['max_width']}px"
            )
        
        if config.height and config.height > self._capabilities["max_height"]:
            raise ScreenshotConfigurationError(
                f"Height {config.height}px exceeds maximum {self._capabilities['max_height']}px"
            )
    
    def _prepare_screenshot_options(self, config: ScreenshotConfig, output_path: Path) -> Dict[str, Any]:
        """Prepare screenshot options for Playwright"""
        screenshot_options = {
            "path": str(output_path),
            "full_page": config.full_page,
            "type": "jpeg" if config.format in ["jpeg", "jpg"] else "png"
        }
        
        # Add quality for JPEG images
        if config.format.lower() in ["jpeg", "jpg"]:
            screenshot_options["quality"] = config.quality
        
        # Add viewport clipping if dimensions specified
        if config.width and config.height:
            screenshot_options["clip"] = {
                "x": 0,
                "y": 0,
                "width": config.width,
                "height": config.height
            }
        
        return screenshot_options
    
    async def _get_file_metadata(self, output_path: Path, config: ScreenshotConfig, start_time: float) -> Dict[str, Any]:
        """Get metadata about the captured screenshot"""
        try:
            file_stat = output_path.stat()
            
            # Get page information if available
            page_info = {}
            try:
                page_info = {
                    "url": self.page.url,
                    "title": await self.page.title(),
                    "viewport": await self.page.evaluate("({width: window.innerWidth, height: window.innerHeight})")
                }
            except Exception as e:
                logger.warning(f"Could not get page info: {str(e)}")
            
            return {
                "file_size": file_stat.st_size,
                "format": config.format,
                "full_page": config.full_page,
                "quality": config.quality if config.format in ["jpeg", "jpg"] else None,
                "dimensions": {
                    "width": config.width,
                    "height": config.height
                } if config.width and config.height else None,
                "capture_time_ms": int((time.time() - start_time) * 1000),
                "page_info": page_info,
                "provider": "playwright"
            }
        except Exception as e:
            logger.warning(f"Could not get file metadata: {str(e)}")
            return {
                "provider": "playwright",
                "error": "metadata_unavailable"
            }