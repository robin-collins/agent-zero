"""
Tests for screenshot provider implementations
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
    ScreenshotProvider,
    ScreenshotTimeoutError,
    ScreenshotUnavailableError,
    ScreenshotConfigurationError
)
from python.helpers.screenshots.providers.playwright_provider import PlaywrightScreenshotProvider

class TestScreenshotConfig:
    """Test ScreenshotConfig validation"""
    
    def test_valid_config(self):
        """Test valid configuration creation"""
        config = ScreenshotConfig(
            full_page=True,
            timeout=5000,
            quality=85,
            format="jpeg",
            width=1920,
            height=1080
        )
        
        assert config.full_page is True
        assert config.timeout == 5000
        assert config.quality == 85
        assert config.format == "jpeg"
        assert config.width == 1920
        assert config.height == 1080
    
    def test_invalid_timeout(self):
        """Test timeout validation"""
        with pytest.raises(ValueError, match="Timeout must be between"):
            ScreenshotConfig(timeout=50)
        
        with pytest.raises(ValueError, match="Timeout must be between"):
            ScreenshotConfig(timeout=50000)
    
    def test_invalid_quality(self):
        """Test quality validation"""
        with pytest.raises(ValueError, match="Quality must be between"):
            ScreenshotConfig(quality=5)
        
        with pytest.raises(ValueError, match="Quality must be between"):
            ScreenshotConfig(quality=105)
    
    def test_invalid_format(self):
        """Test format validation"""
        with pytest.raises(ValueError, match="Format must be"):
            ScreenshotConfig(format="gif")
    
    def test_invalid_dimensions(self):
        """Test dimension validation"""
        with pytest.raises(ValueError, match="Width must be between"):
            ScreenshotConfig(width=0)
        
        with pytest.raises(ValueError, match="Height must be between"):
            ScreenshotConfig(height=20000)

class TestScreenshotResult:
    """Test ScreenshotResult validation"""
    
    def test_valid_success_result(self):
        """Test valid success result"""
        path = Path("/tmp/test.png")
        result = ScreenshotResult(
            success=True,
            path=path,
            metadata={"test": "data"},
            timestamp=time.time()
        )
        
        assert result.success is True
        assert result.path == path
        assert result.metadata == {"test": "data"}
        assert result.error is None
    
    def test_valid_failure_result(self):
        """Test valid failure result"""
        result = ScreenshotResult(
            success=False,
            error="Test error",
            timestamp=time.time()
        )
        
        assert result.success is False
        assert result.error == "Test error"
        assert result.path is None
    
    def test_invalid_success_result(self):
        """Test invalid success result without path"""
        with pytest.raises(ValueError, match="Successful screenshot result must have a path"):
            ScreenshotResult(success=True)
    
    def test_invalid_failure_result(self):
        """Test invalid failure result without error"""
        with pytest.raises(ValueError, match="Failed screenshot result must have an error"):
            ScreenshotResult(success=False)

class TestPlaywrightScreenshotProvider:
    """Test PlaywrightScreenshotProvider"""
    
    @pytest.fixture
    def mock_page(self):
        """Mock Playwright page"""
        mock_page = Mock()
        mock_page.screenshot = AsyncMock()
        mock_page.evaluate = AsyncMock(return_value=2)
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Test Page")
        return mock_page
    
    @pytest.fixture
    def provider(self, mock_page):
        """Create provider instance"""
        return PlaywrightScreenshotProvider(mock_page)
    
    def test_init_valid_page(self, mock_page):
        """Test provider initialization with valid page"""
        provider = PlaywrightScreenshotProvider(mock_page)
        assert provider.page == mock_page
        assert provider._is_available is True
    
    def test_init_invalid_page(self):
        """Test provider initialization with invalid page"""
        with pytest.raises(ValueError, match="Page instance cannot be None"):
            PlaywrightScreenshotProvider(None)
    
    @pytest.mark.asyncio
    async def test_is_available_success(self, provider):
        """Test is_available when page is available"""
        result = await provider.is_available()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_is_available_failure(self, provider):
        """Test is_available when page is not available"""
        provider.page.evaluate.side_effect = Exception("Page disconnected")
        result = await provider.is_available()
        assert result is False
        assert provider._is_available is False
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_success(self, provider, tmp_path):
        """Test successful screenshot capture"""
        # Setup
        config = ScreenshotConfig()
        output_path = tmp_path / "test.png"
        
        # Mock file creation
        def mock_screenshot(**kwargs):
            output_path.touch()
            return None
        
        provider.page.screenshot = AsyncMock(side_effect=mock_screenshot)
        
        # Execute
        result = await provider.capture_screenshot(config, output_path)
        
        # Verify
        assert result.success is True
        assert result.path == output_path
        assert result.error is None
        assert result.metadata is not None
        assert result.metadata["provider"] == "playwright"
        
        # Verify screenshot was called with correct parameters
        provider.page.screenshot.assert_called_once()
        call_args = provider.page.screenshot.call_args[1]
        assert call_args["path"] == str(output_path)
        assert call_args["full_page"] is False
        assert call_args["type"] == "png"
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_timeout(self, provider, tmp_path):
        """Test screenshot capture timeout"""
        config = ScreenshotConfig(timeout=1000)
        output_path = tmp_path / "test.png"
        
        # Mock timeout
        provider.page.screenshot = AsyncMock(side_effect=asyncio.TimeoutError())
        
        # Execute
        result = await provider.capture_screenshot(config, output_path)
        
        # Verify
        assert result.success is False
        assert "timeout" in result.error.lower()
        assert result.path is None
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_unavailable(self, provider, tmp_path):
        """Test screenshot capture when provider unavailable"""
        config = ScreenshotConfig()
        output_path = tmp_path / "test.png"
        
        # Mock unavailable provider
        provider._is_available = False
        provider.page.evaluate = AsyncMock(side_effect=Exception("Disconnected"))
        
        # Execute
        result = await provider.capture_screenshot(config, output_path)
        
        # Verify
        assert result.success is False
        assert "not available" in result.error.lower()
        assert result.path is None
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_jpeg_quality(self, provider, tmp_path):
        """Test JPEG screenshot with quality setting"""
        config = ScreenshotConfig(format="jpeg", quality=75)
        output_path = tmp_path / "test.jpg"
        
        # Mock file creation
        def mock_screenshot(**kwargs):
            output_path.touch()
            return None
        
        provider.page.screenshot = AsyncMock(side_effect=mock_screenshot)
        
        # Execute
        result = await provider.capture_screenshot(config, output_path)
        
        # Verify
        assert result.success is True
        
        # Verify screenshot was called with quality
        call_args = provider.page.screenshot.call_args[1]
        assert call_args["type"] == "jpeg"
        assert call_args["quality"] == 75
    
    @pytest.mark.asyncio
    async def test_capture_screenshot_with_clip(self, provider, tmp_path):
        """Test screenshot with viewport clipping"""
        config = ScreenshotConfig(width=800, height=600)
        output_path = tmp_path / "test.png"
        
        # Mock file creation
        def mock_screenshot(**kwargs):
            output_path.touch()
            return None
        
        provider.page.screenshot = AsyncMock(side_effect=mock_screenshot)
        
        # Execute
        result = await provider.capture_screenshot(config, output_path)
        
        # Verify
        assert result.success is True
        
        # Verify screenshot was called with clip
        call_args = provider.page.screenshot.call_args[1]
        assert "clip" in call_args
        assert call_args["clip"]["width"] == 800
        assert call_args["clip"]["height"] == 600
    
    @pytest.mark.asyncio
    async def test_get_capabilities(self, provider):
        """Test get_capabilities method"""
        capabilities = await provider.get_capabilities()
        
        assert "formats" in capabilities
        assert "png" in capabilities["formats"]
        assert "jpeg" in capabilities["formats"]
        assert "full_page" in capabilities
        assert capabilities["full_page"] is True
        assert "max_timeout" in capabilities
        assert capabilities["max_timeout"] == 30000
    
    @pytest.mark.asyncio
    async def test_cleanup(self, provider):
        """Test cleanup method"""
        await provider.cleanup()
        assert provider._is_available is False
    
    @pytest.mark.asyncio
    async def test_validate_config_invalid_format(self, provider):
        """Test config validation with invalid format"""
        config = ScreenshotConfig(format="gif")  # This should fail in __post_init__
        
        # Since validation happens in __post_init__, we need to catch it there
        with pytest.raises(ValueError):
            await provider._validate_config(config)
    
    @pytest.mark.asyncio
    async def test_validate_config_timeout_too_high(self, provider):
        """Test config validation with timeout too high"""
        config = ScreenshotConfig(timeout=50000)  # Should fail in __post_init__
        
        with pytest.raises(ValueError):
            await provider._validate_config(config)

@pytest.mark.asyncio
async def test_integration_full_workflow():
    """Integration test for complete screenshot workflow"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Setup
        tmp_path = Path(tmp_dir)
        mock_page = Mock()
        mock_page.evaluate = AsyncMock(return_value=2)
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Test Page")
        
        # Mock screenshot that creates a file
        def mock_screenshot(**kwargs):
            output_path = Path(kwargs["path"])
            output_path.touch()
            return None
        
        mock_page.screenshot = AsyncMock(side_effect=mock_screenshot)
        
        # Create provider
        provider = PlaywrightScreenshotProvider(mock_page)
        
        # Test workflow
        assert await provider.is_available() is True
        
        config = ScreenshotConfig(
            full_page=True,
            quality=90,
            format="png",
            timeout=5000
        )
        
        output_path = tmp_path / "integration_test.png"
        result = await provider.capture_screenshot(config, output_path)
        
        # Verify success
        assert result.success is True
        assert result.path == output_path
        assert output_path.exists()
        assert result.metadata is not None
        assert result.metadata["provider"] == "playwright"
        
        # Test capabilities
        capabilities = await provider.get_capabilities()
        assert len(capabilities["formats"]) == 3
        
        # Cleanup
        await provider.cleanup()
        assert provider._is_available is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])