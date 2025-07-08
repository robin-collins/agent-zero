"""
Enhanced Browser Agent with integrated screenshot system
This is a drop-in replacement for browser_agent.py with enhanced screenshot capabilities
"""

import asyncio
import time
from typing import Optional
from agent import Agent, InterventionException
from pathlib import Path

import models
from python.helpers.tool import Tool, Response
from python.helpers import files, defer, persist_chat, strings
from python.helpers.browser_use import browser_use
from python.helpers.print_style import PrintStyle
from python.helpers.playwright import ensure_playwright_binary
from python.extensions.message_loop_start._10_iteration_no import get_iter_no
from pydantic import BaseModel
import uuid
from python.helpers.dirty_json import DirtyJson

# Import new screenshot system
from python.helpers.screenshots import (
    PlaywrightScreenshotProvider,
    BrowserScreenshotManager,
    ScreenshotConfig
)
from python.helpers.screenshots.managers.auto_screenshot_manager import (
    AutoScreenshotManager,
    TriggerType
)
from python.helpers.screenshots.utils.validation_utils import validate_screenshot_config
from python.helpers.settings import get_settings

import logging
logger = logging.getLogger(__name__)

class State:
    @staticmethod
    async def create(agent: Agent):
        state = State(agent)
        return state

    def __init__(self, agent: Agent):
        self.agent = agent
        self.browser_session: Optional[browser_use.BrowserSession] = None
        self.task: Optional[defer.DeferredTask] = None
        self.use_agent: Optional[browser_use.Agent] = None
        self.iter_no = 0
        
        # Enhanced screenshot management
        self.screenshot_manager: Optional[BrowserScreenshotManager] = None
        self.auto_screenshot_manager: Optional[AutoScreenshotManager] = None
        self._screenshot_initialized = False

    def __del__(self):
        self.kill_task()

    async def _initialize(self):
        if self.browser_session:
            return

        # for some reason we need to provide exact path to headless shell, otherwise it looks for headed browser
        pw_binary = ensure_playwright_binary()

        self.browser_session = browser_use.BrowserSession(
            browser_profile=browser_use.BrowserProfile(
                headless=True,
                disable_security=True,
                chromium_sandbox=False,
                accept_downloads=True,
                downloads_dir=files.get_abs_path("tmp/downloads"),
                downloads_path=files.get_abs_path("tmp/downloads"),
                cookies_path=files.get_abs_path("tmp/cookies"),
                viewport={"width": 1280, "height": 720},
                user_agent_type="desktop",
                check_search_results=False,
                max_actions_per_step=10,
                max_failures_per_step=5,
                browser_binary_path=pw_binary,
            ),
            browser_user_data_dir=files.get_abs_path("tmp/browser_user_data"),
            use_vision=self.agent.get_data("_browser_use_vision", False),
            llm_provider=models.get_browser_model(),
            keep_open=True,
        )

        self.use_agent = browser_use.Agent(
            self.browser_session,
            instruction_runner=self.agent.instruction_runner,
            save_to_file=files.get_abs_path("tmp/browser_use.jsonl"),
            save_conversation_history=True,
            injected_content=self.agent.agent_name,
            max_actions_per_step=10,
            max_failures_per_step=5,
            system_message=files.read_file(
                files.get_abs_path("prompts", self.agent.config.prompts_subdir),
                "browser_agent.system.md",
            ),
        )

        # Initialize screenshot system
        await self._initialize_screenshot_system()

    async def _initialize_screenshot_system(self):
        """Initialize the enhanced screenshot system"""
        if self._screenshot_initialized:
            return
        
        try:
            # Get current page
            page = await self.get_page()
            if not page:
                logger.warning("Cannot initialize screenshot system: no page available")
                return
            
            # Create screenshot provider
            provider = PlaywrightScreenshotProvider(page)
            
            # Create screenshot directory
            screenshots_path = Path(files.get_abs_path(
                persist_chat.get_chat_folder_path(self.agent.context.id),
                "browser", "screenshots"
            ))
            
            # Get settings
            settings = get_settings()
            
            # Create browser screenshot manager
            self.screenshot_manager = BrowserScreenshotManager(
                provider=provider,
                base_path=screenshots_path,
                max_age_hours=settings.get("screenshot_cleanup_hours", 24),
                max_files=settings.get("max_screenshot_files", 1000),
                auto_cleanup=settings.get("auto_screenshot", True)
            )
            
            # Initialize manager
            if await self.screenshot_manager.initialize():
                # Create auto screenshot manager
                self.auto_screenshot_manager = AutoScreenshotManager(
                    browser_manager=self.screenshot_manager
                )
                
                # Configure auto screenshot triggers based on settings
                self._configure_auto_screenshots(settings)
                
                self._screenshot_initialized = True
                logger.info("Screenshot system initialized successfully")
            else:
                logger.error("Failed to initialize screenshot manager")
                
        except Exception as e:
            logger.error(f"Failed to initialize screenshot system: {str(e)}")
            self.screenshot_manager = None
            self.auto_screenshot_manager = None

    def _configure_auto_screenshots(self, settings: dict):
        """Configure auto screenshot triggers based on settings"""
        if not self.auto_screenshot_manager:
            return
        
        try:
            # Enable/disable triggers based on settings
            auto_enabled = settings.get("auto_screenshot", True)
            
            # Configure screenshot quality and format
            screenshot_config = ScreenshotConfig(
                quality=settings.get("screenshot_quality", 90),
                format=settings.get("screenshot_format", "png"),
                timeout=settings.get("screenshot_timeout", 3000),
                full_page=False  # Default to viewport screenshots for speed
            )
            
            # Configure triggers
            if auto_enabled:
                self.auto_screenshot_manager.configure_trigger(
                    TriggerType.NAVIGATION,
                    config=screenshot_config
                )
                
                self.auto_screenshot_manager.configure_trigger(
                    TriggerType.INTERACTION,
                    config=screenshot_config
                )
                
                # High quality for errors
                error_config = ScreenshotConfig(
                    quality=95,
                    format="png",
                    timeout=5000,
                    full_page=True
                )
                
                self.auto_screenshot_manager.configure_trigger(
                    TriggerType.ERROR,
                    config=error_config
                )
            
            self.auto_screenshot_manager.set_enabled(auto_enabled)
            
        except Exception as e:
            logger.error(f"Failed to configure auto screenshots: {str(e)}")

    async def get_page(self):
        await self._initialize()
        return await self.browser_session.get_page()

    def kill_task(self):
        if self.task:
            self.task.kill()
            self.task = None

    async def cleanup(self):
        """Enhanced cleanup with screenshot system"""
        try:
            # Cleanup screenshot managers
            if self.auto_screenshot_manager:
                await self.auto_screenshot_manager.cleanup()
                self.auto_screenshot_manager = None
            
            if self.screenshot_manager:
                await self.screenshot_manager.cleanup()
                self.screenshot_manager = None
            
            # Cleanup browser session
            if self.browser_session:
                await self.browser_session.close()
                self.browser_session = None
                
            self.kill_task()
            self._screenshot_initialized = False
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

class BrowserAgent(Tool):
    """Enhanced Browser Agent with integrated screenshot system"""

    async def execute(self, task: str, **kwargs):
        """Execute browser task with enhanced screenshot capabilities"""
        await self.prepare_state()
        
        # Trigger navigation screenshot if we have auto manager
        if self.state.auto_screenshot_manager:
            try:
                await self.state.auto_screenshot_manager.on_navigation(
                    url="task_start",
                    context={"task": task}
                )
            except Exception as e:
                logger.warning(f"Failed to capture navigation screenshot: {str(e)}")

        self.log.update(progress="Starting browser task...")
        
        # Get or create deferred task
        if not self.state.task:
            self.state.task = defer.DeferredTask(self.agent.context.id, timeout=300)

        try:
            # Execute the task
            result = await self.state.task.execute_inside(
                self.state.use_agent.run,
                task
            )
            
            # Trigger completion screenshot
            if self.state.auto_screenshot_manager:
                try:
                    await self.state.auto_screenshot_manager.on_interaction(
                        action="task_completed",
                        context={"task": task, "result": "success"}
                    )
                except Exception as e:
                    logger.warning(f"Failed to capture completion screenshot: {str(e)}")
            
            # Format response
            return await self._format_response(result, task)
            
        except Exception as e:
            # Trigger error screenshot
            if self.state.auto_screenshot_manager:
                try:
                    await self.state.auto_screenshot_manager.on_error(
                        error=str(e),
                        context={"task": task}
                    )
                except Exception as screenshot_e:
                    logger.warning(f"Failed to capture error screenshot: {str(screenshot_e)}")
            
            # Handle error
            logger.error(f"Browser task failed: {str(e)}")
            return Response(
                message=f"Browser task failed: {str(e)}",
                break_loop=False
            )

    async def _format_response(self, result, task: str) -> Response:
        """Format response with enhanced screenshot information"""
        if result.is_done():
            # Task completed successfully
            answer_text = result.final_result()
            
            # Add screenshot information from the new system
            screenshot_info = await self._get_screenshot_info()
            if screenshot_info:
                answer_text += f"\n\n{screenshot_info}"
            
        else:
            # Task hit max_steps without calling done()
            urls = result.urls()
            current_url = urls[-1] if urls else "unknown"
            answer_text = (
                f"Task reached step limit without completion. Last page: {current_url}. "
                f"The browser agent may need clearer instructions on when to finish."
            )
            
            # Still add screenshot info
            screenshot_info = await self._get_screenshot_info()
            if screenshot_info:
                answer_text += f"\n\n{screenshot_info}"

        # Update log
        self.log.update(answer=answer_text)

        return Response(message=answer_text, break_loop=False)

    async def _get_screenshot_info(self) -> Optional[str]:
        """Get screenshot information from the new system"""
        try:
            if self.state.screenshot_manager:
                stats = await self.state.screenshot_manager.get_statistics()
                
                # Get most recent screenshot
                if stats.get("filesystem_stats", {}).get("newest_file"):
                    newest_file = stats["filesystem_stats"]["newest_file"]
                    return f"Latest screenshot: {newest_file['path']}"
                    
        except Exception as e:
            logger.warning(f"Failed to get screenshot info: {str(e)}")
        
        return None

    def get_log_object(self):
        return self.agent.context.log.log(
            type="browser",
            heading=f"icon://captive_portal {self.agent.agent_name}: Calling Browser Agent",
            content="",
            kvps=self.args,
        )

    async def get_update(self):
        """Enhanced get_update with new screenshot system"""
        await self.prepare_state()

        result = {}
        agent = self.agent
        ua = self.state.use_agent
        page = await self.state.get_page()

        if ua and page:
            try:
                async def _get_update():
                    log = []

                    # Get browser use log
                    log.extend(get_use_agent_log(ua))
                    result["log"] = log

                    # Enhanced screenshot capture using new system
                    if self.state.screenshot_manager:
                        try:
                            # Get current settings
                            settings = get_settings()
                            
                            # Create screenshot configuration
                            config = ScreenshotConfig(
                                full_page=False,
                                timeout=settings.get("screenshot_timeout", 3000),
                                quality=settings.get("screenshot_quality", 90),
                                format=settings.get("screenshot_format", "png")
                            )
                            
                            # Capture screenshot with metadata
                            screenshot_result = await self.state.screenshot_manager.capture_with_metadata(
                                config=config,
                                metadata={
                                    "step": len(log),
                                    "agent_id": agent.context.id,
                                    "update_time": time.time(),
                                    "source": "browser_agent_update"
                                }
                            )
                            
                            if screenshot_result["success"]:
                                result["screenshot"] = screenshot_result["screenshot"]
                                result["screenshot_metadata"] = screenshot_result.get("metadata", {})
                                
                                # Update log with screenshot
                                self.log.update(screenshot=screenshot_result["screenshot"])
                            else:
                                logger.warning(f"Screenshot capture failed: {screenshot_result.get('error', 'unknown')}")
                                result["screenshot_error"] = screenshot_result.get("error", "unknown")
                                
                        except Exception as e:
                            logger.error(f"Enhanced screenshot capture failed: {str(e)}")
                            # Fallback to original screenshot logic
                            result["screenshot_error"] = f"Enhanced screenshot failed: {str(e)}"
                    else:
                        # Fallback to original screenshot logic if new system not available
                        try:
                            path = files.get_abs_path(
                                persist_chat.get_chat_folder_path(agent.context.id),
                                "browser",
                                "screenshots",
                                f"{uuid.uuid4()}.png",
                            )
                            files.make_dirs(path)
                            await page.screenshot(path=path, full_page=False, timeout=3000)
                            result["screenshot"] = f"img://{path}&t={str(time.time())}"
                        except Exception as e:
                            logger.warning(f"Fallback screenshot failed: {str(e)}")
                            result["screenshot_error"] = f"Screenshot failed: {str(e)}"

                if self.state.task and not self.state.task.is_ready():
                    await self.state.task.execute_inside(_get_update)

            except Exception as e:
                logger.error(f"Error in get_update: {str(e)}")
                result["error"] = str(e)

        return result

    async def prepare_state(self, reset=False):
        """Enhanced state preparation with screenshot system"""
        self.state = self.agent.get_data("_browser_agent_state")
        if reset and self.state:
            await self.state.cleanup()
            self.state = None

        if not self.state:
            self.state = await State.create(self.agent)
            self.agent.set_data("_browser_agent_state", self.state)

    def cleanup_history(self):
        """Clean up browser history with enhanced screenshot awareness"""
        def cleanup_message(msg):
            if not msg.ai and isinstance(msg.content, dict) and "tool_name" in msg.content and str(msg.content["tool_name"]).startswith("browser_"):
                if not msg.summary:
                    msg.summary = "browser content removed to save space"

        for msg in self.agent.history.current.messages:
            cleanup_message(msg)
        
        for prev in self.agent.history.topics:
            if not prev.summary:
                for msg in prev.messages:
                    cleanup_message(msg)

    async def get_screenshot_statistics(self) -> dict:
        """Get screenshot statistics from the enhanced system"""
        await self.prepare_state()
        
        if self.state.screenshot_manager:
            try:
                stats = await self.state.screenshot_manager.get_statistics()
                
                # Add auto screenshot stats if available
                if self.state.auto_screenshot_manager:
                    auto_stats = self.state.auto_screenshot_manager.get_statistics()
                    stats["auto_screenshot_stats"] = auto_stats
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get screenshot statistics: {str(e)}")
                return {"error": str(e)}
        
        return {"error": "Screenshot manager not available"}

    async def manual_screenshot(self, config: Optional[dict] = None) -> dict:
        """Manually capture a screenshot with custom configuration"""
        await self.prepare_state()
        
        if not self.state.screenshot_manager:
            return {"success": False, "error": "Screenshot manager not available"}
        
        try:
            # Parse configuration
            screenshot_config = ScreenshotConfig()
            if config:
                screenshot_config.full_page = config.get("full_page", False)
                screenshot_config.quality = config.get("quality", 90)
                screenshot_config.format = config.get("format", "png")
                screenshot_config.timeout = config.get("timeout", 3000)
                
                # Validate configuration
                issues = validate_screenshot_config(screenshot_config)
                if issues:
                    return {"success": False, "error": f"Invalid configuration: {', '.join(issues)}"}
            
            # Capture screenshot
            result = await self.state.screenshot_manager.capture_with_metadata(
                config=screenshot_config,
                metadata={
                    "manual_capture": True,
                    "agent_id": self.agent.context.id,
                    "timestamp": time.time()
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Manual screenshot failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def cleanup_screenshots(self, dry_run: bool = False) -> dict:
        """Manually cleanup old screenshots"""
        await self.prepare_state()
        
        if not self.state.screenshot_manager:
            return {"success": False, "error": "Screenshot manager not available"}
        
        try:
            return await self.state.screenshot_manager.manual_cleanup(dry_run=dry_run)
        except Exception as e:
            logger.error(f"Screenshot cleanup failed: {str(e)}")
            return {"success": False, "error": str(e)}

# Helper functions
def get_use_agent_log(ua):
    """Get log from browser use agent"""
    log = []
    try:
        if ua and hasattr(ua, 'message_manager'):
            for message in ua.message_manager.get_messages():
                if hasattr(message, 'content'):
                    log.append(str(message.content))
    except Exception as e:
        logger.warning(f"Failed to get browser use log: {str(e)}")
    return log

# Export for backward compatibility
__all__ = ['BrowserAgent', 'State']