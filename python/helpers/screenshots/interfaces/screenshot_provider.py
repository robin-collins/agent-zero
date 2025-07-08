"""
Screenshot provider interface following SOLID principles
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScreenshotConfig:
    """Configuration for screenshot capture with validation"""
    full_page: bool = False
    timeout: int = 3000
    quality: int = 90
    format: str = "png"
    width: Optional[int] = None
    height: Optional[int] = None
    
    def __post_init__(self):
        """Validate configuration parameters"""
        if self.timeout < 100 or self.timeout > 30000:
            raise ValueError(f"Timeout must be between 100 and 30000ms, got {self.timeout}")
        
        if self.quality < 10 or self.quality > 100:
            raise ValueError(f"Quality must be between 10 and 100, got {self.quality}")
        
        if self.format not in ["png", "jpeg", "jpg"]:
            raise ValueError(f"Format must be 'png', 'jpeg', or 'jpg', got {self.format}")
        
        if self.width is not None and (self.width <= 0 or self.width > 10000):
            raise ValueError(f"Width must be between 1 and 10000 pixels, got {self.width}")
        
        if self.height is not None and (self.height <= 0 or self.height > 10000):
            raise ValueError(f"Height must be between 1 and 10000 pixels, got {self.height}")

@dataclass
class ScreenshotResult:
    """Result of screenshot operation with comprehensive information"""
    success: bool
    path: Optional[Path] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    
    def __post_init__(self):
        """Validate result state"""
        if self.success and self.path is None:
            raise ValueError("Successful screenshot result must have a path")
        
        if not self.success and self.error is None:
            raise ValueError("Failed screenshot result must have an error message")

class ScreenshotProvider(ABC):
    """Abstract base class for screenshot providers following ISP"""
    
    @abstractmethod
    async def capture_screenshot(
        self, 
        config: ScreenshotConfig,
        output_path: Path
    ) -> ScreenshotResult:
        """
        Capture a screenshot with given configuration
        
        Args:
            config: Screenshot configuration
            output_path: Path where screenshot should be saved
            
        Returns:
            ScreenshotResult with success status and metadata
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if provider is available and ready to capture screenshots
        
        Returns:
            True if provider is ready, False otherwise
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources used by the provider
        Must be called when provider is no longer needed
        """
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """
        Get provider capabilities and supported features
        
        Returns:
            Dictionary of capabilities
        """
        pass

class ScreenshotProviderError(Exception):
    """Base exception for screenshot provider errors"""
    pass

class ScreenshotTimeoutError(ScreenshotProviderError):
    """Raised when screenshot capture times out"""
    pass

class ScreenshotUnavailableError(ScreenshotProviderError):
    """Raised when screenshot provider is not available"""
    pass

class ScreenshotConfigurationError(ScreenshotProviderError):
    """Raised when screenshot configuration is invalid"""
    pass