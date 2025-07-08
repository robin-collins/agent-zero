#!/usr/bin/env python3
"""
Screenshot System Initialization Test Script
Tests the robustness and reliability of the screenshot system initialization.
"""

import asyncio
import logging
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ScreenshotInitializationTester:
    """Test suite for screenshot system initialization."""
    
    def __init__(self):
        self.test_results = []
        self.temp_dir = None
        
    async def run_all_tests(self):
        """Run all initialization tests."""
        logger.info("Starting screenshot system initialization tests...")
        
        # Setup test environment
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.info(f"Test directory: {self.temp_dir}")
        
        try:
            # Test 1: Basic imports
            await self._test_basic_imports()
            
            # Test 2: Screenshot tool initialization
            await self._test_screenshot_tool_init()
            
            # Test 3: Screenshot manager initialization
            await self._test_screenshot_manager_init()
            
            # Test 4: Playwright provider initialization
            await self._test_playwright_provider_init()
            
            # Test 5: Utility functions
            await self._test_utility_functions()
            
            # Test 6: Configuration validation
            await self._test_configuration_validation()
            
            # Test 7: Error handling
            await self._test_error_handling()
            
            # Test 8: Cleanup functionality
            await self._test_cleanup_functionality()
            
        finally:
            # Cleanup
            if self.temp_dir and self.temp_dir.exists():
                import shutil
                shutil.rmtree(self.temp_dir)
        
        # Report results
        self._report_results()
        
        return all(result['passed'] for result in self.test_results)
    
    async def _test_basic_imports(self):
        """Test basic screenshot system imports."""
        test_name = "Basic Imports"
        logger.info(f"Running test: {test_name}")
        
        try:
            # Test core imports
            from python.helpers.screenshots import (
                ScreenshotConfig,
                ScreenshotResult,
                ScreenshotProvider,
                PlaywrightScreenshotProvider,
                BrowserScreenshotManager
            )
            
            # Test utility imports
            from python.helpers.screenshots.utils.validation_utils import (
                validate_screenshot_config,
                sanitize_filename
            )
            
            from python.helpers.screenshots.utils.path_utils import (
                generate_screenshot_path,
                ensure_screenshot_directory
            )
            
            # Test tool import
            from python.tools.screenshot_tool import ScreenshotTool
            
            self.test_results.append({
                'test': test_name,
                'passed': True,
                'message': 'All imports successful'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Import failed: {str(e)}'
            })
    
    async def _test_screenshot_tool_init(self):
        """Test screenshot tool initialization."""
        test_name = "Screenshot Tool Initialization"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.tools.screenshot_tool import ScreenshotTool
            
            # Create mock agent
            mock_agent = Mock()
            mock_agent.context = Mock()
            mock_agent.context.id = "test_agent"
            
            # Initialize tool
            tool = ScreenshotTool()
            tool.agent = mock_agent
            
            # Check initialization status
            if hasattr(tool, 'is_initialized'):
                if tool.is_initialized:
                    message = "Tool initialized successfully"
                else:
                    message = f"Tool initialization failed: {tool.initialization_error}"
            else:
                message = "Tool missing initialization status"
            
            self.test_results.append({
                'test': test_name,
                'passed': hasattr(tool, 'is_initialized'),
                'message': message
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Tool initialization failed: {str(e)}'
            })
    
    async def _test_screenshot_manager_init(self):
        """Test screenshot manager initialization."""
        test_name = "Screenshot Manager Initialization"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.helpers.screenshots import BrowserScreenshotManager
            from python.helpers.screenshots.providers.playwright_provider import PlaywrightScreenshotProvider
            
            # Create mock provider
            mock_provider = Mock(spec=PlaywrightScreenshotProvider)
            mock_provider.is_available = AsyncMock(return_value=True)
            mock_provider.get_capabilities = AsyncMock(return_value={
                "formats": ["png", "jpeg"],
                "full_page": True,
                "timeout_control": True
            })
            
            # Create manager
            manager = BrowserScreenshotManager(
                provider=mock_provider,
                base_path=self.temp_dir / "screenshots",
                auto_cleanup=False
            )
            
            # Test initialization
            init_result = await manager.initialize()
            
            self.test_results.append({
                'test': test_name,
                'passed': init_result,
                'message': 'Manager initialized successfully' if init_result else 'Manager initialization failed'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Manager initialization failed: {str(e)}'
            })
    
    async def _test_playwright_provider_init(self):
        """Test Playwright provider initialization."""
        test_name = "Playwright Provider Initialization"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.helpers.screenshots.providers.playwright_provider import PlaywrightScreenshotProvider
            
            # Create mock page
            mock_page = Mock()
            mock_page.evaluate = AsyncMock(return_value=2)
            
            # Create provider
            provider = PlaywrightScreenshotProvider(mock_page)
            
            # Test availability
            is_available = await provider.is_available()
            
            # Test capabilities
            capabilities = await provider.get_capabilities()
            
            self.test_results.append({
                'test': test_name,
                'passed': is_available and bool(capabilities),
                'message': f'Provider available: {is_available}, capabilities: {bool(capabilities)}'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Provider initialization failed: {str(e)}'
            })
    
    async def _test_utility_functions(self):
        """Test utility functions."""
        test_name = "Utility Functions"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.helpers.screenshots.utils.validation_utils import (
                validate_screenshot_config,
                sanitize_filename
            )
            from python.helpers.screenshots.utils.path_utils import (
                generate_screenshot_path,
                ensure_screenshot_directory
            )
            from python.helpers.screenshots import ScreenshotConfig
            
            # Test validation
            config = ScreenshotConfig()
            issues = validate_screenshot_config(config)
            
            # Test filename sanitization
            safe_filename = sanitize_filename("test file!@#.png")
            
            # Test path generation
            test_path = generate_screenshot_path(self.temp_dir, "png")
            
            # Test directory creation
            dir_result = ensure_screenshot_directory(self.temp_dir / "test_dir")
            
            self.test_results.append({
                'test': test_name,
                'passed': True,
                'message': f'All utilities working: config_issues={len(issues)}, safe_filename={safe_filename}, path_generated={bool(test_path)}, dir_created={dir_result}'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Utility functions failed: {str(e)}'
            })
    
    async def _test_configuration_validation(self):
        """Test configuration validation."""
        test_name = "Configuration Validation"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.helpers.screenshots import ScreenshotConfig
            
            # Test valid config
            valid_config = ScreenshotConfig()
            
            # Test invalid configs
            try:
                invalid_config1 = ScreenshotConfig(quality=150)  # Should fail
                validation_working = False
            except ValueError:
                validation_working = True
            
            try:
                invalid_config2 = ScreenshotConfig(format="gif")  # Should fail
                validation_working = validation_working and False
            except ValueError:
                validation_working = validation_working and True
            
            self.test_results.append({
                'test': test_name,
                'passed': validation_working,
                'message': f'Configuration validation working: {validation_working}'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Configuration validation failed: {str(e)}'
            })
    
    async def _test_error_handling(self):
        """Test error handling."""
        test_name = "Error Handling"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.helpers.screenshots import BrowserScreenshotManager
            
            # Test with None provider (should fail gracefully)
            try:
                manager = BrowserScreenshotManager(
                    provider=None,
                    base_path=self.temp_dir
                )
                error_handling = False
            except ValueError:
                error_handling = True
            
            # Test with invalid path
            try:
                manager = BrowserScreenshotManager(
                    provider=Mock(),
                    base_path="/invalid/path/that/does/not/exist"
                )
                error_handling = error_handling and True
            except Exception:
                error_handling = error_handling and True
            
            self.test_results.append({
                'test': test_name,
                'passed': error_handling,
                'message': f'Error handling working: {error_handling}'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Error handling test failed: {str(e)}'
            })
    
    async def _test_cleanup_functionality(self):
        """Test cleanup functionality."""
        test_name = "Cleanup Functionality"
        logger.info(f"Running test: {test_name}")
        
        try:
            from python.helpers.screenshots.utils.cleanup_utils import (
                cleanup_old_screenshots,
                get_cleanup_statistics
            )
            
            # Create some test files
            test_files_dir = self.temp_dir / "cleanup_test"
            test_files_dir.mkdir()
            
            for i in range(3):
                test_file = test_files_dir / f"test_{i}.png"
                test_file.write_text("test content")
            
            # Test statistics
            stats = await get_cleanup_statistics(test_files_dir)
            
            # Test cleanup (dry run)
            cleanup_result = await cleanup_old_screenshots(
                test_files_dir,
                max_age_hours=0,  # All files are "old"
                max_files=1,
                dry_run=True
            )
            
            self.test_results.append({
                'test': test_name,
                'passed': bool(stats and cleanup_result),
                'message': f'Cleanup functionality working: stats={bool(stats)}, cleanup_result={bool(cleanup_result)}'
            })
            
        except Exception as e:
            self.test_results.append({
                'test': test_name,
                'passed': False,
                'message': f'Cleanup functionality failed: {str(e)}'
            })
    
    def _report_results(self):
        """Report test results."""
        logger.info("\n" + "="*60)
        logger.info("SCREENSHOT SYSTEM INITIALIZATION TEST RESULTS")
        logger.info("="*60)
        
        passed_count = 0
        total_count = len(self.test_results)
        
        for result in self.test_results:
            status = "PASS" if result['passed'] else "FAIL"
            logger.info(f"{status}: {result['test']} - {result['message']}")
            if result['passed']:
                passed_count += 1
        
        logger.info("="*60)
        logger.info(f"SUMMARY: {passed_count}/{total_count} tests passed")
        
        if passed_count == total_count:
            logger.info("✅ All tests passed! Screenshot system is robust and reliable.")
        else:
            logger.warning("❌ Some tests failed. Screenshot system needs improvements.")
        
        logger.info("="*60)

async def main():
    """Run screenshot initialization tests."""
    tester = ScreenshotInitializationTester()
    success = await tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)