"""
Tests for screenshot manager implementations
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import time

# Add project root to path
import sys
sys.path.insert(0, '/mnt/d/a0/agent-zero')

from python.helpers.screenshots.interfaces.screenshot_provider import (
    ScreenshotConfig,
    ScreenshotResult,
    ScreenshotProvider
)
from python.helpers.screenshots.managers.browser_screenshot_manager import BrowserScreenshotManager
from python.helpers.screenshots.managers.auto_screenshot_manager import (
    AutoScreenshotManager,
    TriggerType,
    ScreenshotTrigger
)

class MockProvider(ScreenshotProvider):
    """Mock screenshot provider for testing"""
    
    def __init__(self):
        self.available = True
        self.screenshots = []
        self.fail_next = False
    
    async def capture_screenshot(self, config: ScreenshotConfig, output_path: Path) -> ScreenshotResult:
        if self.fail_next:
            self.fail_next = False
            return ScreenshotResult(
                success=False,
                error="Mock failure",
                timestamp=time.time()
            )
        
        # Create mock file
        output_path.touch()
        
        result = ScreenshotResult(
            success=True,
            path=output_path,
            metadata={"mock": True, "config": config.format},
            timestamp=time.time()
        )
        
        self.screenshots.append(result)
        return result
    
    async def is_available(self) -> bool:
        return self.available
    
    async def cleanup(self) -> None:
        self.available = False
        self.screenshots.clear()
    
    async def get_capabilities(self) -> dict:
        return {
            "formats": ["png", "jpeg"],
            "full_page": True,
            "max_timeout": 30000
        }

class TestBrowserScreenshotManager:
    """Test BrowserScreenshotManager"""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock provider"""
        return MockProvider()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def manager(self, mock_provider, temp_dir):
        """Create manager instance"""
        return BrowserScreenshotManager(
            provider=mock_provider,
            base_path=temp_dir,
            max_age_hours=1,
            max_files=10,
            auto_cleanup=False  # Disable for testing
        )
    
    def test_init_valid_params(self, mock_provider, temp_dir):
        """Test manager initialization with valid parameters"""
        manager = BrowserScreenshotManager(
            provider=mock_provider,
            base_path=temp_dir,
            max_age_hours=24,
            max_files=1000
        )
        
        assert manager.provider == mock_provider
        assert manager.base_path == temp_dir
        assert manager.max_age_hours == 24
        assert manager.max_files == 1000
        assert manager._initialized is False
    
    def test_init_invalid_provider(self, temp_dir):
        """Test manager initialization with invalid provider"""
        with pytest.raises(ValueError, match="Provider cannot be None"):
            BrowserScreenshotManager(
                provider=None,
                base_path=temp_dir
            )
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, manager, mock_provider):
        """Test successful initialization"""
        result = await manager.initialize()
        
        assert result is True
        assert manager._initialized is True
        assert manager.base_path.exists()
    
    @pytest.mark.asyncio
    async def test_initialize_provider_unavailable(self, manager, mock_provider):
        """Test initialization with unavailable provider"""
        mock_provider.available = False
        
        result = await manager.initialize()
        
        assert result is False
        assert manager._initialized is False
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_success(self, manager):
        """Test successful screenshot capture"""
        await manager.initialize()
        
        config = ScreenshotConfig(format="png")
        result = await manager.capture_screenshot(config)
        
        assert result.success is True
        assert result.path is not None
        assert result.path.exists()
        assert result.metadata is not None
        assert result.metadata["manager"] == "browser_screenshot_manager"
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_custom_filename(self, manager):
        """Test screenshot capture with custom filename"""
        await manager.initialize()
        
        result = await manager.capture_screenshot(
            custom_filename="test_custom.png"
        )
        
        assert result.success is True
        assert result.path.name == "test_custom.png"
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_not_initialized(self, manager):
        """Test screenshot capture without initialization"""
        # Don't call initialize()
        result = await manager.capture_screenshot()
        
        # Should auto-initialize and succeed
        assert result.success is True
        assert manager._initialized is True
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_provider_failure(self, manager, mock_provider):
        """Test screenshot capture with provider failure"""
        await manager.initialize()
        mock_provider.fail_next = True
        
        result = await manager.capture_screenshot()
        
        assert result.success is False
        assert result.error == "Mock failure"
    
    @pytest.mark.asyncio
    async def test_capture_with_metadata(self, manager):
        """Test capture_with_metadata method"""
        await manager.initialize()
        
        result = await manager.capture_with_metadata(
            metadata={"test": "data"}
        )
        
        assert result["success"] is True
        assert "screenshot" in result
        assert result["screenshot"].startswith("img://")
        assert "timestamp" in result
        assert result["manager"] == "browser_screenshot_manager"
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, manager):
        """Test get_statistics method"""
        await manager.initialize()
        
        # Capture some screenshots
        await manager.capture_screenshot()
        await manager.capture_screenshot()
        
        stats = await manager.get_statistics()
        
        assert "manager_stats" in stats
        assert stats["manager_stats"]["total_screenshots"] == 2
        assert stats["manager_stats"]["successful_screenshots"] == 2
        assert "filesystem_stats" in stats
        assert "provider_capabilities" in stats
        assert "configuration" in stats
        assert "status" in stats
    
    @pytest.mark.asyncio
    async def test_manual_cleanup(self, manager):
        """Test manual cleanup"""
        await manager.initialize()
        
        # Capture some screenshots
        await manager.capture_screenshot()
        await manager.capture_screenshot()
        
        # Run dry run cleanup
        result = await manager.manual_cleanup(dry_run=True)
        
        assert "cleaned_files" in result
        assert "kept_files" in result
        assert "total_cleaned" in result
        assert result["dry_run"] is True
    
    @pytest.mark.asyncio
    async def test_screenshot_session_context_manager(self, manager):
        """Test screenshot session context manager"""
        await manager.initialize()
        
        session_config = ScreenshotConfig(format="jpeg")
        
        async with manager.screenshot_session(session_config) as capture:
            result1 = await capture()
            result2 = await capture(metadata={"step": 2})
            
            assert result1.success is True
            assert result2.success is True
            assert result2.metadata["session_screenshot"] == 2
    
    @pytest.mark.asyncio
    async def test_cleanup(self, manager, mock_provider):
        """Test manager cleanup"""
        await manager.initialize()
        
        await manager.cleanup()
        
        assert manager._initialized is False
        assert mock_provider.available is False
    
    @pytest.mark.asyncio
    async def test_async_context_manager(self, mock_provider, temp_dir):
        """Test async context manager"""
        async with BrowserScreenshotManager(
            provider=mock_provider,
            base_path=temp_dir,
            auto_cleanup=False
        ) as manager:
            assert manager._initialized is True
            
            result = await manager.capture_screenshot()
            assert result.success is True
        
        assert manager._initialized is False

class TestAutoScreenshotManager:
    """Test AutoScreenshotManager"""
    
    @pytest.fixture
    def mock_provider(self):
        """Create mock provider"""
        return MockProvider()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    @pytest.fixture
    def browser_manager(self, mock_provider, temp_dir):
        """Create browser manager"""
        return BrowserScreenshotManager(
            provider=mock_provider,
            base_path=temp_dir,
            auto_cleanup=False
        )
    
    @pytest.fixture
    def auto_manager(self, browser_manager):
        """Create auto manager"""
        return AutoScreenshotManager(browser_manager)
    
    def test_init_valid_params(self, browser_manager):
        """Test auto manager initialization"""
        manager = AutoScreenshotManager(browser_manager)
        
        assert manager.browser_manager == browser_manager
        assert len(manager.triggers) > 0
        assert manager._enabled is True
    
    def test_init_invalid_manager(self):
        """Test auto manager initialization with invalid manager"""
        with pytest.raises(ValueError, match="Browser manager cannot be None"):
            AutoScreenshotManager(None)
    
    @pytest.mark.asyncio
    async def test_trigger_screenshot_success(self, auto_manager):
        """Test successful screenshot trigger"""
        await auto_manager.browser_manager.initialize()
        
        result = await auto_manager.trigger_screenshot(
            TriggerType.NAVIGATION,
            context={"url": "https://example.com"}
        )
        
        assert result is not None
        assert result.success is True
        assert result.metadata["trigger_type"] == "navigation"
        assert result.metadata["auto_capture"] is True
    
    @pytest.mark.asyncio
    async def test_trigger_screenshot_disabled(self, auto_manager):
        """Test screenshot trigger when disabled"""
        auto_manager.set_enabled(False)
        
        result = await auto_manager.trigger_screenshot(TriggerType.NAVIGATION)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_trigger_screenshot_force(self, auto_manager):
        """Test screenshot trigger with force"""
        await auto_manager.browser_manager.initialize()
        auto_manager.set_enabled(False)
        
        result = await auto_manager.trigger_screenshot(
            TriggerType.NAVIGATION,
            force=True
        )
        
        assert result is not None
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_on_navigation(self, auto_manager):
        """Test on_navigation event handler"""
        await auto_manager.browser_manager.initialize()
        
        result = await auto_manager.on_navigation(
            "https://example.com",
            context={"step": "login"}
        )
        
        assert result is not None
        assert result.success is True
        assert result.metadata["url"] == "https://example.com"
        assert result.metadata["step"] == "login"
    
    @pytest.mark.asyncio
    async def test_on_error(self, auto_manager):
        """Test on_error event handler"""
        await auto_manager.browser_manager.initialize()
        
        result = await auto_manager.on_error(
            "Test error",
            context={"severity": "high"}
        )
        
        assert result is not None
        assert result.success is True
        assert result.metadata["error"] == "Test error"
        assert result.metadata["severity"] == "high"
    
    @pytest.mark.asyncio
    async def test_on_interaction(self, auto_manager):
        """Test on_interaction event handler"""
        await auto_manager.browser_manager.initialize()
        
        result = await auto_manager.on_interaction(
            "click",
            context={"element": "button"}
        )
        
        assert result is not None
        assert result.success is True
        assert result.metadata["action"] == "click"
        assert result.metadata["element"] == "button"
    
    @pytest.mark.asyncio
    async def test_on_timeout(self, auto_manager):
        """Test on_timeout event handler"""
        await auto_manager.browser_manager.initialize()
        
        result = await auto_manager.on_timeout({
            "timeout": 5000,
            "operation": "page_load"
        })
        
        assert result is not None
        assert result.success is True
        assert result.metadata["timeout"] == 5000
        assert result.metadata["operation"] == "page_load"
    
    def test_enable_disable_trigger(self, auto_manager):
        """Test enable/disable trigger"""
        # Initially navigation trigger should be enabled
        nav_trigger = auto_manager._find_trigger(TriggerType.NAVIGATION)
        assert nav_trigger.enabled is True
        
        # Disable navigation trigger
        auto_manager.enable_trigger(TriggerType.NAVIGATION, False)
        assert nav_trigger.enabled is False
        
        # Re-enable navigation trigger
        auto_manager.enable_trigger(TriggerType.NAVIGATION, True)
        assert nav_trigger.enabled is True
    
    def test_configure_trigger(self, auto_manager):
        """Test configure trigger"""
        new_config = ScreenshotConfig(format="jpeg", quality=95)
        
        auto_manager.configure_trigger(
            TriggerType.NAVIGATION,
            config=new_config,
            metadata={"custom": "metadata"}
        )
        
        nav_trigger = auto_manager._find_trigger(TriggerType.NAVIGATION)
        assert nav_trigger.config.format == "jpeg"
        assert nav_trigger.config.quality == 95
        assert nav_trigger.metadata["custom"] == "metadata"
    
    def test_get_statistics(self, auto_manager):
        """Test get_statistics method"""
        stats = auto_manager.get_statistics()
        
        assert "auto_stats" in stats
        assert "configuration" in stats
        assert "triggers" in stats
        assert "history_size" in stats
        
        # Check trigger configuration
        triggers = stats["triggers"]
        assert len(triggers) > 0
        assert all("type" in t for t in triggers)
        assert all("enabled" in t for t in triggers)
    
    def test_get_recent_screenshots(self, auto_manager):
        """Test get_recent_screenshots method"""
        # Initially should be empty
        recent = auto_manager.get_recent_screenshots()
        assert len(recent) == 0
        
        # Add some mock history
        auto_manager._screenshot_history = [
            {
                "timestamp": time.time(),
                "trigger_type": "navigation",
                "success": True,
                "path": "/test/path.png"
            }
        ]
        
        recent = auto_manager.get_recent_screenshots(limit=5)
        assert len(recent) == 1
        assert recent[0]["trigger_type"] == "navigation"
    
    @pytest.mark.asyncio
    async def test_duplicate_detection(self, auto_manager):
        """Test duplicate screenshot detection"""
        await auto_manager.browser_manager.initialize()
        
        # First screenshot should succeed
        result1 = await auto_manager.trigger_screenshot(TriggerType.NAVIGATION)
        assert result1 is not None
        
        # Immediate duplicate should be skipped
        result2 = await auto_manager.trigger_screenshot(TriggerType.NAVIGATION)
        assert result2 is None
        
        # Check statistics
        stats = auto_manager.get_statistics()
        assert stats["auto_stats"]["duplicate_screenshots"] > 0
    
    @pytest.mark.asyncio
    async def test_cleanup(self, auto_manager):
        """Test auto manager cleanup"""
        await auto_manager.cleanup()
        
        assert auto_manager._enabled is False
        assert len(auto_manager._screenshot_history) == 0

@pytest.mark.asyncio
async def test_integration_full_workflow():
    """Integration test for complete manager workflow"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Setup
        tmp_path = Path(tmp_dir)
        mock_provider = MockProvider()
        
        # Create browser manager
        browser_manager = BrowserScreenshotManager(
            provider=mock_provider,
            base_path=tmp_path,
            max_age_hours=1,
            max_files=10,
            auto_cleanup=False
        )
        
        # Create auto manager
        auto_manager = AutoScreenshotManager(browser_manager)
        
        # Initialize
        await browser_manager.initialize()
        
        # Test various triggers
        nav_result = await auto_manager.on_navigation("https://example.com")
        error_result = await auto_manager.on_error("Test error")
        interact_result = await auto_manager.on_interaction("click")
        
        # Verify all succeeded
        assert nav_result.success is True
        assert error_result.success is True
        assert interact_result.success is True
        
        # Check statistics
        stats = await browser_manager.get_statistics()
        assert stats["manager_stats"]["total_screenshots"] == 3
        
        auto_stats = auto_manager.get_statistics()
        assert auto_stats["auto_stats"]["auto_screenshots"] == 3
        
        # Test cleanup
        await auto_manager.cleanup()
        await browser_manager.cleanup()
        
        assert not mock_provider.available

if __name__ == "__main__":
    pytest.main([__file__, "-v"])