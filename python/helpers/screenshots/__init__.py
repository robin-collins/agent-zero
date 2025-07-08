"""
Screenshot module for Agent Zero
Provides modular screenshot capture capabilities following SOLID principles
"""

from .interfaces.screenshot_provider import ScreenshotProvider, ScreenshotConfig, ScreenshotResult
from .providers.playwright_provider import PlaywrightScreenshotProvider
from .managers.browser_screenshot_manager import BrowserScreenshotManager

__all__ = [
    'ScreenshotProvider',
    'ScreenshotConfig', 
    'ScreenshotResult',
    'PlaywrightScreenshotProvider',
    'BrowserScreenshotManager'
]

__version__ = "1.0.0"