"""
Browser screenshot manager with comprehensive error handling and resource management
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import time
import asyncio
import logging
from contextlib import asynccontextmanager

from ..interfaces.screenshot_provider import (
    ScreenshotProvider,
    ScreenshotConfig,
    ScreenshotResult
)
from ..utils.path_utils import generate_screenshot_path, ensure_screenshot_directory
from ..utils.cleanup_utils import cleanup_old_screenshots, get_cleanup_statistics
from ..utils.validation_utils import validate_screenshot_config, validate_base_path

logger = logging.getLogger(__name__)

class BrowserScreenshotManager:
    """
    Manages browser screenshots with configurable providers and automatic cleanup
    Follows SOLID principles with dependency injection and single responsibility
    """
    
    def __init__(
        self,
        provider: ScreenshotProvider,
        base_path: Path,
        max_age_hours: int = 24,
        max_files: int = 1000,
        auto_cleanup: bool = True
    ):
        """
        Initialize screenshot manager
        
        Args:
            provider: Screenshot provider instance
            base_path: Base directory for screenshots
            max_age_hours: Maximum age before cleanup
            max_files: Maximum number of files to keep
            auto_cleanup: Whether to automatically clean up old files
        """
        if not provider:
            raise ValueError("Provider cannot be None")
        
        self.provider = provider
        self.base_path = Path(base_path)
        self.max_age_hours = max_age_hours
        self.max_files = max_files
        self.auto_cleanup = auto_cleanup
        
        # State management
        self._initialized = False
        self._cleanup_task = None
        self._screenshot_count = 0
        self._last_cleanup = 0
        
        # Statistics
        self._stats = {
            "total_screenshots": 0,
            "successful_screenshots": 0,
            "failed_screenshots": 0,
            "cleanup_runs": 0,
            "space_freed": 0
        }
        
        # Validate base path
        try:
            validate_base_path(self.base_path)
        except ValueError as e:
            logger.error(f"Invalid base path: {str(e)}")
            raise
    
    async def initialize(self) -> bool:
        """
        Initialize the screenshot manager
        
        Returns:
            True if initialization successful
        """
        if self._initialized:
            return True
        
        try:
            # Ensure directory exists
            if not ensure_screenshot_directory(self.base_path):
                logger.error(f"Failed to create screenshot directory: {self.base_path}")
                return False
            
            # Check provider availability
            if not await self.provider.is_available():
                logger.error("Screenshot provider is not available")
                return False
            
            # Start cleanup task if auto cleanup is enabled
            if self.auto_cleanup:
                await self._start_cleanup_task()
            
            self._initialized = True
            logger.info(f"Screenshot manager initialized with base path: {self.base_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize screenshot manager: {str(e)}")
            return False
    
    async def capture_screenshot(
        self,
        config: Optional[ScreenshotConfig] = None,
        custom_filename: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ScreenshotResult:
        """
        Capture a screenshot with optional custom configuration
        
        Args:
            config: Screenshot configuration (uses default if None)
            custom_filename: Custom filename (generates if None)
            metadata: Additional metadata to include
            
        Returns:
            ScreenshotResult with capture information
        """
        if not self._initialized:
            if not await self.initialize():
                return ScreenshotResult(
                    success=False,
                    error="Screenshot manager not initialized",
                    timestamp=time.time()
                )
        
        # Use default config if none provided
        if config is None:
            config = ScreenshotConfig()
        
        # Validate configuration
        config_issues = validate_screenshot_config(config)
        if config_issues:
            error_msg = f"Invalid configuration: {', '.join(config_issues)}"
            logger.error(error_msg)
            return ScreenshotResult(
                success=False,
                error=error_msg,
                timestamp=time.time()
            )
        
        # Generate output path
        if custom_filename:
            # Sanitize custom filename
            from ..utils.validation_utils import sanitize_filename
            safe_filename = sanitize_filename(custom_filename)
            output_path = self.base_path / safe_filename
        else:
            output_path = generate_screenshot_path(
                self.base_path, 
                config.format,
                prefix=f"auto_{self._screenshot_count}"
            )
        
        # Update statistics
        self._stats["total_screenshots"] += 1
        self._screenshot_count += 1
        
        # Capture screenshot
        try:
            result = await self.provider.capture_screenshot(config, output_path)
            
            # Update statistics
            if result.success:
                self._stats["successful_screenshots"] += 1
                logger.info(f"Screenshot captured: {result.path}")
            else:
                self._stats["failed_screenshots"] += 1
                logger.error(f"Screenshot failed: {result.error}")
            
            # Add manager metadata
            if result.success and result.metadata:
                result.metadata.update({
                    "manager": "browser_screenshot_manager",
                    "screenshot_number": self._screenshot_count,
                    "base_path": str(self.base_path)
                })
                
                if metadata:
                    result.metadata.update(metadata)
            
            # Schedule cleanup if needed
            if self.auto_cleanup and self._should_cleanup():
                asyncio.create_task(self._run_cleanup())
            
            return result
            
        except Exception as e:
            self._stats["failed_screenshots"] += 1
            logger.error(f"Unexpected error during screenshot capture: {str(e)}")
            return ScreenshotResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                timestamp=time.time()
            )
    
    async def capture_with_metadata(
        self,
        config: Optional[ScreenshotConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Capture screenshot and return formatted metadata for agent logging
        
        Args:
            config: Screenshot configuration
            metadata: Additional metadata
            
        Returns:
            Dictionary with screenshot information for agent logging
        """
        result = await self.capture_screenshot(config, metadata=metadata)
        
        response = {
            "success": result.success,
            "timestamp": result.timestamp or time.time(),
            "manager": "browser_screenshot_manager"
        }
        
        if result.success:
            response["screenshot"] = f"img://{result.path}&t={response['timestamp']}"
            response["path"] = str(result.path)
            
            if result.metadata:
                response["metadata"] = result.metadata
        else:
            response["error"] = result.error
        
        if metadata:
            response.update(metadata)
        
        return response
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get manager statistics and file system information
        
        Returns:
            Dictionary with comprehensive statistics
        """
        try:
            # Get file system statistics
            fs_stats = await get_cleanup_statistics(self.base_path)
            
            # Get provider capabilities
            provider_caps = await self.provider.get_capabilities()
            
            # Combine all statistics
            return {
                "manager_stats": self._stats.copy(),
                "filesystem_stats": fs_stats,
                "provider_capabilities": provider_caps,
                "configuration": {
                    "base_path": str(self.base_path),
                    "max_age_hours": self.max_age_hours,
                    "max_files": self.max_files,
                    "auto_cleanup": self.auto_cleanup
                },
                "status": {
                    "initialized": self._initialized,
                    "provider_available": await self.provider.is_available(),
                    "cleanup_running": self._cleanup_task is not None and not self._cleanup_task.done()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {
                "manager_stats": self._stats.copy(),
                "error": str(e)
            }
    
    async def manual_cleanup(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Manually trigger cleanup operation
        
        Args:
            dry_run: If True, only report what would be cleaned
            
        Returns:
            Cleanup results
        """
        try:
            logger.info(f"Starting manual cleanup (dry_run={dry_run})")
            
            result = await cleanup_old_screenshots(
                self.base_path,
                self.max_age_hours,
                self.max_files,
                dry_run=dry_run
            )
            
            if not dry_run:
                self._stats["cleanup_runs"] += 1
                self._stats["space_freed"] += result.get("space_freed", 0)
                self._last_cleanup = time.time()
            
            logger.info(f"Manual cleanup completed: {result['total_cleaned']} files")
            return result
            
        except Exception as e:
            logger.error(f"Manual cleanup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """
        Clean up manager resources
        """
        logger.info("Cleaning up screenshot manager")
        
        # Stop cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clean up provider
        if self.provider:
            await self.provider.cleanup()
        
        self._initialized = False
        logger.info("Screenshot manager cleanup completed")
    
    @asynccontextmanager
    async def screenshot_session(self, config: Optional[ScreenshotConfig] = None):
        """
        Context manager for screenshot session with automatic cleanup
        
        Args:
            config: Default configuration for the session
            
        Yields:
            Screenshot capture function
        """
        session_config = config or ScreenshotConfig()
        session_count = 0
        
        async def capture_in_session(
            override_config: Optional[ScreenshotConfig] = None,
            metadata: Optional[Dict[str, Any]] = None
        ) -> ScreenshotResult:
            nonlocal session_count
            session_count += 1
            
            final_config = override_config or session_config
            final_metadata = metadata or {}
            final_metadata.update({
                "session_screenshot": session_count,
                "session_id": id(self)
            })
            
            return await self.capture_screenshot(final_config, metadata=final_metadata)
        
        try:
            logger.info("Starting screenshot session")
            yield capture_in_session
        finally:
            logger.info(f"Ending screenshot session ({session_count} screenshots)")
    
    def _should_cleanup(self) -> bool:
        """
        Check if cleanup should be triggered based on time and screenshot count
        
        Returns:
            True if cleanup should be run
        """
        current_time = time.time()
        
        # Check time since last cleanup
        time_since_cleanup = current_time - self._last_cleanup
        if time_since_cleanup < 3600:  # Don't cleanup more than once per hour
            return False
        
        # Check screenshot count
        if self._screenshot_count % 50 == 0:  # Every 50 screenshots
            return True
        
        # Check time interval
        if time_since_cleanup > 6 * 3600:  # Every 6 hours
            return True
        
        return False
    
    async def _start_cleanup_task(self) -> None:
        """
        Start background cleanup task
        """
        if self._cleanup_task and not self._cleanup_task.done():
            return
        
        self._cleanup_task = asyncio.create_task(self._background_cleanup())
    
    async def _background_cleanup(self) -> None:
        """
        Background cleanup task that runs periodically
        """
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour
                
                if self._should_cleanup():
                    await self._run_cleanup()
                    
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
        except Exception as e:
            logger.error(f"Background cleanup error: {str(e)}")
    
    async def _run_cleanup(self) -> None:
        """
        Run cleanup operation
        """
        try:
            result = await cleanup_old_screenshots(
                self.base_path,
                self.max_age_hours,
                self.max_files
            )
            
            self._stats["cleanup_runs"] += 1
            self._stats["space_freed"] += result.get("space_freed", 0)
            self._last_cleanup = time.time()
            
            if result.get("total_cleaned", 0) > 0:
                logger.info(f"Cleanup completed: {result['total_cleaned']} files removed")
                
        except Exception as e:
            logger.error(f"Cleanup failed: {str(e)}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()