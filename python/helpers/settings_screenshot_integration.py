"""
Screenshot settings integration for Agent Zero
This module provides screenshot-related settings that can be integrated into the main settings system
"""

from typing import Dict, List, Any
from python.helpers.settings import SettingsField, SettingsSection
from python.helpers.screenshots.utils.validation_utils import validate_screenshot_settings

def get_screenshot_settings_fields(settings: Dict[str, Any]) -> List[SettingsField]:
    """
    Get screenshot-related settings fields
    
    Args:
        settings: Current settings dictionary
        
    Returns:
        List of screenshot settings fields
    """
    fields = []
    
    # Auto Screenshot setting
    fields.append({
        "id": "auto_screenshot",
        "title": "Auto Screenshot",
        "description": "Automatically capture screenshots during browser sessions. This helps with debugging and provides visual context for browser interactions.",
        "type": "switch",
        "value": settings.get("auto_screenshot", True),
    })
    
    # Screenshot Quality setting
    fields.append({
        "id": "screenshot_quality",
        "title": "Screenshot Quality",
        "description": "JPEG quality for screenshots (10-100). Higher values produce better quality but larger files. Only applies to JPEG format.",
        "type": "number",
        "value": settings.get("screenshot_quality", 90),
        "min": 10,
        "max": 100,
    })
    
    # Screenshot Format setting
    fields.append({
        "id": "screenshot_format",
        "title": "Screenshot Format",
        "description": "Default format for screenshots. PNG provides lossless compression, JPEG is smaller but lossy.",
        "type": "select",
        "value": settings.get("screenshot_format", "png"),
        "options": [
            {"value": "png", "label": "PNG (Lossless)"},
            {"value": "jpeg", "label": "JPEG (Smaller file size)"},
        ],
    })
    
    # Screenshot Timeout setting
    fields.append({
        "id": "screenshot_timeout",
        "title": "Screenshot Timeout",
        "description": "Timeout for screenshot capture in milliseconds. Higher values may be needed for complex pages but increase wait time.",
        "type": "number",
        "value": settings.get("screenshot_timeout", 3000),
        "min": 1000,
        "max": 30000,
    })
    
    # Screenshot Cleanup Hours setting
    fields.append({
        "id": "screenshot_cleanup_hours",
        "title": "Cleanup After Hours",
        "description": "Remove screenshots older than this many hours. Helps manage disk space usage.",
        "type": "number",
        "value": settings.get("screenshot_cleanup_hours", 24),
        "min": 1,
        "max": 168,  # 1 week
    })
    
    # Max Screenshot Files setting
    fields.append({
        "id": "max_screenshot_files",
        "title": "Max Screenshot Files",
        "description": "Maximum number of screenshot files to keep. Older files are removed when this limit is exceeded.",
        "type": "number",
        "value": settings.get("max_screenshot_files", 1000),
        "min": 10,
        "max": 10000,
    })
    
    # Screenshot Auto Triggers setting
    fields.append({
        "id": "screenshot_triggers",
        "title": "Auto Triggers",
        "description": "Configure when screenshots are automatically captured",
        "type": "group",
        "fields": [
            {
                "id": "screenshot_trigger_navigation",
                "title": "On Navigation",
                "description": "Capture screenshot when navigating to new pages",
                "type": "switch",
                "value": settings.get("screenshot_trigger_navigation", True),
            },
            {
                "id": "screenshot_trigger_interaction",
                "title": "On Interaction",
                "description": "Capture screenshot after user interactions (clicks, form submissions, etc.)",
                "type": "switch",
                "value": settings.get("screenshot_trigger_interaction", True),
            },
            {
                "id": "screenshot_trigger_error",
                "title": "On Error",
                "description": "Capture screenshot when errors occur (full page, high quality)",
                "type": "switch",
                "value": settings.get("screenshot_trigger_error", True),
            },
        ]
    })
    
    # Screenshot Storage setting
    fields.append({
        "id": "screenshot_storage",
        "title": "Storage Settings",
        "description": "Configure screenshot storage behavior",
        "type": "group",
        "fields": [
            {
                "id": "screenshot_create_metadata",
                "title": "Create Metadata",
                "description": "Store detailed metadata about each screenshot",
                "type": "switch",
                "value": settings.get("screenshot_create_metadata", True),
            },
            {
                "id": "screenshot_compress_old",
                "title": "Compress Old Screenshots",
                "description": "Compress screenshots older than 7 days to save space",
                "type": "switch",
                "value": settings.get("screenshot_compress_old", False),
            },
        ]
    })
    
    return fields

def get_screenshot_settings_section(settings: Dict[str, Any]) -> SettingsSection:
    """
    Get screenshot settings section
    
    Args:
        settings: Current settings dictionary
        
    Returns:
        Screenshot settings section
    """
    fields = get_screenshot_settings_fields(settings)
    
    section: SettingsSection = {
        "id": "screenshot",
        "title": "Screenshot Settings",
        "description": "Configure automatic screenshot capture during browser sessions. Screenshots help with debugging and provide visual context for browser interactions.",
        "fields": fields,
        "tab": "agent",
    }
    
    return section

def validate_screenshot_settings_update(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate screenshot settings update
    
    Args:
        settings: New settings to validate
        
    Returns:
        Validation result with any issues
    """
    # Extract screenshot-related settings
    screenshot_settings = {}
    screenshot_keys = [
        "auto_screenshot", "screenshot_quality", "screenshot_format", 
        "screenshot_timeout", "screenshot_cleanup_hours", "max_screenshot_files",
        "screenshot_trigger_navigation", "screenshot_trigger_interaction", 
        "screenshot_trigger_error", "screenshot_create_metadata", "screenshot_compress_old"
    ]
    
    for key in screenshot_keys:
        if key in settings:
            screenshot_settings[key] = settings[key]
    
    # Validate settings
    if screenshot_settings:
        return validate_screenshot_settings(screenshot_settings)
    
    return {"valid": True, "issues": [], "warnings": [], "sanitized_settings": {}}

def get_screenshot_settings_defaults() -> Dict[str, Any]:
    """
    Get default screenshot settings
    
    Returns:
        Dictionary of default screenshot settings
    """
    return {
        "auto_screenshot": True,
        "screenshot_quality": 90,
        "screenshot_format": "png",
        "screenshot_timeout": 3000,
        "screenshot_cleanup_hours": 24,
        "max_screenshot_files": 1000,
        "screenshot_trigger_navigation": True,
        "screenshot_trigger_interaction": True,
        "screenshot_trigger_error": True,
        "screenshot_create_metadata": True,
        "screenshot_compress_old": False,
    }

def merge_screenshot_settings(current_settings: Dict[str, Any], new_settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge screenshot settings with validation
    
    Args:
        current_settings: Current settings
        new_settings: New settings to merge
        
    Returns:
        Merged settings dictionary
    """
    merged = current_settings.copy()
    
    # Validate new settings
    validation_result = validate_screenshot_settings_update(new_settings)
    
    if validation_result["valid"]:
        # Merge validated settings
        merged.update(validation_result["sanitized_settings"])
    else:
        # Log validation errors but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid screenshot settings: {validation_result['issues']}")
        
        # Use defaults for invalid settings
        defaults = get_screenshot_settings_defaults()
        for key, value in new_settings.items():
            if key.startswith("screenshot_") and key in defaults:
                merged[key] = defaults[key]
    
    return merged

def get_screenshot_settings_help() -> Dict[str, str]:
    """
    Get help text for screenshot settings
    
    Returns:
        Dictionary mapping setting IDs to help text
    """
    return {
        "auto_screenshot": "When enabled, screenshots are automatically captured during browser sessions. This provides visual context for debugging and helps understand what the browser agent is doing.",
        
        "screenshot_quality": "Controls the quality of JPEG screenshots. Higher values (90-100) produce better quality but larger files. Lower values (30-70) create smaller files but may have visible compression artifacts. This setting only affects JPEG format.",
        
        "screenshot_format": "PNG format provides lossless compression and is recommended for screenshots with text or sharp edges. JPEG format produces smaller files but uses lossy compression, which may blur text slightly.",
        
        "screenshot_timeout": "Maximum time to wait for screenshot capture. Complex pages may need longer timeouts, but this increases the time between browser actions. 3000ms (3 seconds) is usually sufficient.",
        
        "screenshot_cleanup_hours": "Screenshots older than this many hours are automatically deleted to manage disk space. Consider your debugging needs when setting this value.",
        
        "max_screenshot_files": "Maximum number of screenshot files to keep. When this limit is exceeded, older files are deleted. This provides an additional safeguard against excessive disk usage.",
        
        "screenshot_trigger_navigation": "Automatically capture a screenshot when the browser navigates to a new page. Useful for tracking the browser's journey through different pages.",
        
        "screenshot_trigger_interaction": "Capture a screenshot after user interactions like clicks, form submissions, or text input. Helps verify that actions had the expected effect.",
        
        "screenshot_trigger_error": "Capture a high-quality, full-page screenshot when errors occur. Essential for debugging browser agent issues.",
        
        "screenshot_create_metadata": "Store detailed metadata about each screenshot including timestamp, page URL, file size, and capture context. Useful for analysis but uses additional disk space.",
        
        "screenshot_compress_old": "Compress screenshots older than 7 days to save disk space. This is a future feature that will reduce storage requirements for long-term screenshot retention."
    }

# Integration helper functions for existing settings system
def integrate_screenshot_settings(settings_function):
    """
    Decorator to integrate screenshot settings into existing settings function
    
    Args:
        settings_function: Original get_settings_fields function
        
    Returns:
        Enhanced settings function with screenshot settings
    """
    def wrapper(*args, **kwargs):
        result = settings_function(*args, **kwargs)
        
        # Add screenshot section to existing sections
        if "sections" in result:
            # Get current settings for defaults
            from python.helpers.settings import get_settings
            current_settings = get_settings()
            
            # Create screenshot section
            screenshot_section = get_screenshot_settings_section(current_settings)
            
            # Insert screenshot section after browser_model_section
            sections = result["sections"]
            insert_index = len(sections)  # Default to end
            
            for i, section in enumerate(sections):
                if section.get("id") == "browser_model":
                    insert_index = i + 1
                    break
            
            sections.insert(insert_index, screenshot_section)
        
        return result
    
    return wrapper

# Export for use in main settings system
__all__ = [
    'get_screenshot_settings_fields',
    'get_screenshot_settings_section', 
    'validate_screenshot_settings_update',
    'get_screenshot_settings_defaults',
    'merge_screenshot_settings',
    'get_screenshot_settings_help',
    'integrate_screenshot_settings'
]