"""
Auto screenshot manager for intelligent screenshot capture
"""

from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import time
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass

from ..interfaces.screenshot_provider import (
    ScreenshotProvider,
    ScreenshotConfig,
    ScreenshotResult
)
from .browser_screenshot_manager import BrowserScreenshotManager

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    """Types of screenshot triggers"""
    NAVIGATION = "navigation"
    ERROR = "error"
    INTERACTION = "interaction"
    TIMEOUT = "timeout"
    MANUAL = "manual"
    PERIODIC = "periodic"

@dataclass
class ScreenshotTrigger:
    """Configuration for screenshot triggers"""
    trigger_type: TriggerType
    enabled: bool = True
    config: Optional[ScreenshotConfig] = None
    condition: Optional[Callable] = None
    metadata: Optional[Dict[str, Any]] = None

class AutoScreenshotManager:
    """
    Manages automatic screenshot capture based on various triggers
    Extends BrowserScreenshotManager with intelligent capture logic
    """
    
    def __init__(
        self,
        browser_manager: BrowserScreenshotManager,
        triggers: Optional[List[ScreenshotTrigger]] = None
    ):
        """
        Initialize auto screenshot manager
        
        Args:
            browser_manager: Base browser screenshot manager
            triggers: List of screenshot triggers
        """
        if not browser_manager:
            raise ValueError("Browser manager cannot be None")
        
        self.browser_manager = browser_manager
        self.triggers = triggers or self._get_default_triggers()
        
        # State management
        self._last_screenshot_time = 0
        self._screenshot_history = []
        self._enabled = True
        
        # Statistics
        self._auto_stats = {
            "auto_screenshots": 0,
            "triggered_by": {},
            "skipped_screenshots": 0,
            "duplicate_screenshots": 0
        }
        
        # Configuration
        self._min_interval = 1.0  # Minimum seconds between screenshots
        self._max_history = 100  # Maximum history entries to keep
        self._duplicate_threshold = 5.0  # Seconds to consider duplicates
    
    def _get_default_triggers(self) -> List[ScreenshotTrigger]:
        """
        Get default screenshot triggers
        
        Returns:
            List of default triggers
        """
        return [
            ScreenshotTrigger(
                trigger_type=TriggerType.NAVIGATION,
                enabled=True,
                config=ScreenshotConfig(full_page=False, timeout=3000),
                metadata={"trigger": "navigation"}
            ),
            ScreenshotTrigger(
                trigger_type=TriggerType.ERROR,
                enabled=True,
                config=ScreenshotConfig(full_page=True, timeout=5000),
                metadata={"trigger": "error", "priority": "high"}
            ),
            ScreenshotTrigger(
                trigger_type=TriggerType.INTERACTION,
                enabled=True,
                config=ScreenshotConfig(full_page=False, timeout=2000),
                metadata={"trigger": "interaction"}
            ),
            ScreenshotTrigger(
                trigger_type=TriggerType.PERIODIC,
                enabled=False,  # Disabled by default
                config=ScreenshotConfig(full_page=False, timeout=3000),
                metadata={"trigger": "periodic"}
            )
        ]
    
    async def trigger_screenshot(
        self,
        trigger_type: TriggerType,
        context: Optional[Dict[str, Any]] = None,
        force: bool = False
    ) -> Optional[ScreenshotResult]:
        """
        Trigger a screenshot based on type and context
        
        Args:
            trigger_type: Type of trigger
            context: Additional context information
            force: Force screenshot even if conditions not met
            
        Returns:
            ScreenshotResult if screenshot was taken, None if skipped
        """
        if not self._enabled and not force:
            return None
        
        # Find matching trigger
        trigger = self._find_trigger(trigger_type)
        if not trigger or not trigger.enabled:
            self._auto_stats["skipped_screenshots"] += 1
            return None
        
        # Check conditions
        if not force and not self._should_capture(trigger, context):
            self._auto_stats["skipped_screenshots"] += 1
            return None
        
        # Prepare metadata
        metadata = trigger.metadata.copy() if trigger.metadata else {}
        if context:
            metadata.update(context)
        
        metadata.update({
            "auto_capture": True,
            "trigger_type": trigger_type.value,
            "timestamp": time.time()
        })
        
        # Capture screenshot
        try:
            result = await self.browser_manager.capture_screenshot(
                config=trigger.config,
                metadata=metadata
            )
            
            if result.success:
                self._auto_stats["auto_screenshots"] += 1
                self._auto_stats["triggered_by"][trigger_type.value] = \
                    self._auto_stats["triggered_by"].get(trigger_type.value, 0) + 1
                
                # Update history
                self._update_history(trigger_type, result)
                
                logger.info(f"Auto screenshot captured: {trigger_type.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Auto screenshot failed: {str(e)}")
            return ScreenshotResult(
                success=False,
                error=str(e),
                timestamp=time.time()
            )
    
    async def on_navigation(self, url: str, context: Optional[Dict[str, Any]] = None) -> Optional[ScreenshotResult]:
        """
        Handle navigation event
        
        Args:
            url: New URL
            context: Additional context
            
        Returns:
            ScreenshotResult if screenshot was taken
        """
        nav_context = {"url": url, "event": "navigation"}
        if context:
            nav_context.update(context)
        
        return await self.trigger_screenshot(TriggerType.NAVIGATION, nav_context)
    
    async def on_error(self, error: str, context: Optional[Dict[str, Any]] = None) -> Optional[ScreenshotResult]:
        """
        Handle error event
        
        Args:
            error: Error message
            context: Additional context
            
        Returns:
            ScreenshotResult if screenshot was taken
        """
        error_context = {"error": error, "event": "error"}
        if context:
            error_context.update(context)
        
        return await self.trigger_screenshot(TriggerType.ERROR, error_context)
    
    async def on_interaction(self, action: str, context: Optional[Dict[str, Any]] = None) -> Optional[ScreenshotResult]:
        """
        Handle interaction event
        
        Args:
            action: Action performed
            context: Additional context
            
        Returns:
            ScreenshotResult if screenshot was taken
        """
        interaction_context = {"action": action, "event": "interaction"}
        if context:
            interaction_context.update(context)
        
        return await self.trigger_screenshot(TriggerType.INTERACTION, interaction_context)
    
    async def on_timeout(self, timeout_info: Dict[str, Any]) -> Optional[ScreenshotResult]:
        """
        Handle timeout event
        
        Args:
            timeout_info: Timeout information
            
        Returns:
            ScreenshotResult if screenshot was taken
        """
        timeout_context = {"event": "timeout"}
        timeout_context.update(timeout_info)
        
        return await self.trigger_screenshot(TriggerType.TIMEOUT, timeout_context)
    
    async def capture_periodic(self, interval: float = 30.0) -> None:
        """
        Start periodic screenshot capture
        
        Args:
            interval: Interval in seconds between screenshots
        """
        logger.info(f"Starting periodic screenshots (interval: {interval}s)")
        
        try:
            while self._enabled:
                await asyncio.sleep(interval)
                
                if self._enabled:
                    await self.trigger_screenshot(
                        TriggerType.PERIODIC,
                        {"interval": interval}
                    )
                    
        except asyncio.CancelledError:
            logger.info("Periodic screenshot capture cancelled")
        except Exception as e:
            logger.error(f"Periodic screenshot error: {str(e)}")
    
    def enable_trigger(self, trigger_type: TriggerType, enabled: bool = True) -> None:
        """
        Enable or disable specific trigger
        
        Args:
            trigger_type: Type of trigger to modify
            enabled: Whether to enable the trigger
        """
        trigger = self._find_trigger(trigger_type)
        if trigger:
            trigger.enabled = enabled
            logger.info(f"Trigger {trigger_type.value} {'enabled' if enabled else 'disabled'}")
    
    def configure_trigger(
        self,
        trigger_type: TriggerType,
        config: Optional[ScreenshotConfig] = None,
        condition: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Configure specific trigger
        
        Args:
            trigger_type: Type of trigger to configure
            config: Screenshot configuration
            condition: Condition function
            metadata: Additional metadata
        """
        trigger = self._find_trigger(trigger_type)
        if trigger:
            if config:
                trigger.config = config
            if condition:
                trigger.condition = condition
            if metadata:
                trigger.metadata = metadata
            
            logger.info(f"Trigger {trigger_type.value} configured")
    
    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable auto screenshot manager
        
        Args:
            enabled: Whether to enable auto screenshots
        """
        self._enabled = enabled
        logger.info(f"Auto screenshots {'enabled' if enabled else 'disabled'}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get auto screenshot statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "auto_stats": self._auto_stats.copy(),
            "configuration": {
                "enabled": self._enabled,
                "min_interval": self._min_interval,
                "max_history": self._max_history,
                "duplicate_threshold": self._duplicate_threshold
            },
            "triggers": [
                {
                    "type": trigger.trigger_type.value,
                    "enabled": trigger.enabled,
                    "config": {
                        "full_page": trigger.config.full_page if trigger.config else None,
                        "timeout": trigger.config.timeout if trigger.config else None,
                        "format": trigger.config.format if trigger.config else None
                    }
                }
                for trigger in self.triggers
            ],
            "history_size": len(self._screenshot_history)
        }
    
    def get_recent_screenshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent auto screenshots
        
        Args:
            limit: Maximum number of screenshots to return
            
        Returns:
            List of recent screenshot information
        """
        return self._screenshot_history[-limit:] if self._screenshot_history else []
    
    def _find_trigger(self, trigger_type: TriggerType) -> Optional[ScreenshotTrigger]:
        """
        Find trigger by type
        
        Args:
            trigger_type: Type to find
            
        Returns:
            Matching trigger or None
        """
        for trigger in self.triggers:
            if trigger.trigger_type == trigger_type:
                return trigger
        return None
    
    def _should_capture(self, trigger: ScreenshotTrigger, context: Optional[Dict[str, Any]]) -> bool:
        """
        Check if screenshot should be captured based on trigger conditions
        
        Args:
            trigger: Trigger configuration
            context: Current context
            
        Returns:
            True if screenshot should be captured
        """
        current_time = time.time()
        
        # Check minimum interval
        if current_time - self._last_screenshot_time < self._min_interval:
            return False
        
        # Check custom condition
        if trigger.condition:
            try:
                if not trigger.condition(context):
                    return False
            except Exception as e:
                logger.warning(f"Trigger condition error: {str(e)}")
                return False
        
        # Check for duplicates
        if self._is_duplicate_request(trigger.trigger_type, context):
            self._auto_stats["duplicate_screenshots"] += 1
            return False
        
        return True
    
    def _is_duplicate_request(self, trigger_type: TriggerType, context: Optional[Dict[str, Any]]) -> bool:
        """
        Check if this is a duplicate screenshot request
        
        Args:
            trigger_type: Type of trigger
            context: Request context
            
        Returns:
            True if this is likely a duplicate
        """
        if not self._screenshot_history:
            return False
        
        current_time = time.time()
        
        # Check recent history for similar requests
        for entry in reversed(self._screenshot_history[-5:]):  # Check last 5 entries
            if entry["trigger_type"] == trigger_type.value:
                if current_time - entry["timestamp"] < self._duplicate_threshold:
                    # Similar request within threshold
                    return True
        
        return False
    
    def _update_history(self, trigger_type: TriggerType, result: ScreenshotResult) -> None:
        """
        Update screenshot history
        
        Args:
            trigger_type: Type of trigger
            result: Screenshot result
        """
        current_time = time.time()
        
        entry = {
            "timestamp": current_time,
            "trigger_type": trigger_type.value,
            "success": result.success,
            "path": str(result.path) if result.path else None,
            "error": result.error
        }
        
        self._screenshot_history.append(entry)
        self._last_screenshot_time = current_time
        
        # Trim history if too long
        if len(self._screenshot_history) > self._max_history:
            self._screenshot_history = self._screenshot_history[-self._max_history:]
    
    async def cleanup(self) -> None:
        """
        Clean up auto screenshot manager
        """
        logger.info("Cleaning up auto screenshot manager")
        self._enabled = False
        
        # Clear history
        self._screenshot_history.clear()
        
        # Clean up browser manager
        if self.browser_manager:
            await self.browser_manager.cleanup()