"""
Validation utilities for screenshot operations
"""

from pathlib import Path
from typing import Union, List, Dict, Any
import logging
import re

from ..interfaces.screenshot_provider import ScreenshotConfig, ScreenshotConfigurationError

logger = logging.getLogger(__name__)

def validate_screenshot_path(path: Union[str, Path], base_path: Union[str, Path]) -> bool:
    """
    Validate screenshot path for security and correctness
    
    Args:
        path: Path to validate
        base_path: Base directory that path should be within
        
    Returns:
        True if path is valid and safe
        
    Raises:
        ValueError: If path is invalid or unsafe
    """
    try:
        if isinstance(path, str):
            path = Path(path)
        if isinstance(base_path, str):
            base_path = Path(base_path)
        
        # Resolve paths to handle relative components
        path = path.resolve()
        base_path = base_path.resolve()
        
        # Check if path is within base directory (prevent directory traversal)
        try:
            path.relative_to(base_path)
        except ValueError:
            raise ValueError(f"Path {path} is outside allowed base directory {base_path}")
        
        # Check path length
        if len(str(path)) > 260:  # Windows MAX_PATH limit
            raise ValueError(f"Path too long: {len(str(path))} characters")
        
        # Check for invalid characters
        invalid_chars = '<>:"|?*'
        if any(char in str(path) for char in invalid_chars):
            raise ValueError(f"Path contains invalid characters: {invalid_chars}")
        
        # Check filename
        filename = path.name
        if not filename:
            raise ValueError("Path must include a filename")
        
        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        if filename.upper().split('.')[0] in reserved_names:
            raise ValueError(f"Filename '{filename}' is a reserved name")
        
        # Check file extension
        valid_extensions = {'.png', '.jpg', '.jpeg'}
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f"Invalid file extension '{path.suffix}'. Must be one of: {valid_extensions}")
        
        return True
        
    except Exception as e:
        logger.error(f"Path validation failed: {str(e)}")
        raise ValueError(f"Invalid screenshot path: {str(e)}")

def validate_screenshot_config(config: ScreenshotConfig) -> List[str]:
    """
    Validate screenshot configuration and return list of issues
    
    Args:
        config: Configuration to validate
        
    Returns:
        List of validation issues (empty if valid)
    """
    issues = []
    
    try:
        # Validate timeout
        if config.timeout < 100:
            issues.append("Timeout too low (minimum 100ms)")
        elif config.timeout > 60000:
            issues.append("Timeout too high (maximum 60000ms)")
        
        # Validate quality
        if config.quality < 1:
            issues.append("Quality too low (minimum 1)")
        elif config.quality > 100:
            issues.append("Quality too high (maximum 100)")
        
        # Validate format
        valid_formats = {"png", "jpeg", "jpg"}
        if config.format not in valid_formats:
            issues.append(f"Invalid format '{config.format}'. Must be one of: {valid_formats}")
        
        # Validate dimensions
        if config.width is not None:
            if config.width <= 0:
                issues.append("Width must be positive")
            elif config.width > 10000:
                issues.append("Width too large (maximum 10000px)")
        
        if config.height is not None:
            if config.height <= 0:
                issues.append("Height must be positive")
            elif config.height > 10000:
                issues.append("Height too large (maximum 10000px)")
        
        # Validate dimension consistency
        if (config.width is None) != (config.height is None):
            issues.append("Both width and height must be specified together")
        
        # Validate quality for format
        if config.format in ["jpeg", "jpg"] and config.quality < 10:
            issues.append("JPEG quality should be at least 10 for reasonable results")
        
        return issues
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        return [f"Validation error: {str(e)}"]

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to ensure it's safe for filesystem
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    try:
        # Remove or replace invalid characters
        invalid_chars = '<>:"|?*\\/'
        sanitized = filename
        
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Ensure filename is not empty
        if not sanitized:
            sanitized = "screenshot"
        
        # Limit length
        if len(sanitized) > 100:
            name_part = sanitized[:90]
            ext_part = sanitized[-10:] if '.' in sanitized[-10:] else ''
            sanitized = name_part + ext_part
        
        # Ensure it doesn't start with a dot (hidden file)
        if sanitized.startswith('.'):
            sanitized = 'screenshot_' + sanitized[1:]
        
        return sanitized
        
    except Exception as e:
        logger.error(f"Filename sanitization failed: {str(e)}")
        return "screenshot_sanitized"

def validate_screenshot_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate screenshot settings from configuration
    
    Args:
        settings: Dictionary of settings to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "issues": [],
        "warnings": [],
        "sanitized_settings": {}
    }
    
    try:
        # Default settings
        defaults = {
            "auto_screenshot": True,
            "screenshot_quality": 90,
            "screenshot_format": "png",
            "screenshot_cleanup_hours": 24,
            "max_screenshot_files": 1000,
            "screenshot_timeout": 3000
        }
        
        sanitized = defaults.copy()
        
        # Validate each setting
        for key, value in settings.items():
            if key == "auto_screenshot":
                if not isinstance(value, bool):
                    result["issues"].append(f"auto_screenshot must be boolean, got {type(value)}")
                    result["valid"] = False
                else:
                    sanitized[key] = value
            
            elif key == "screenshot_quality":
                try:
                    quality = int(value)
                    if quality < 1 or quality > 100:
                        result["issues"].append("screenshot_quality must be between 1 and 100")
                        result["valid"] = False
                    else:
                        sanitized[key] = quality
                except (ValueError, TypeError):
                    result["issues"].append(f"screenshot_quality must be integer, got {type(value)}")
                    result["valid"] = False
            
            elif key == "screenshot_format":
                if value not in ["png", "jpeg", "jpg"]:
                    result["issues"].append(f"screenshot_format must be 'png', 'jpeg', or 'jpg', got '{value}'")
                    result["valid"] = False
                else:
                    sanitized[key] = value
            
            elif key == "screenshot_cleanup_hours":
                try:
                    hours = int(value)
                    if hours < 1 or hours > 168:  # 1 week max
                        result["issues"].append("screenshot_cleanup_hours must be between 1 and 168")
                        result["valid"] = False
                    else:
                        sanitized[key] = hours
                except (ValueError, TypeError):
                    result["issues"].append(f"screenshot_cleanup_hours must be integer, got {type(value)}")
                    result["valid"] = False
            
            elif key == "max_screenshot_files":
                try:
                    max_files = int(value)
                    if max_files < 10 or max_files > 10000:
                        result["issues"].append("max_screenshot_files must be between 10 and 10000")
                        result["valid"] = False
                    else:
                        sanitized[key] = max_files
                except (ValueError, TypeError):
                    result["issues"].append(f"max_screenshot_files must be integer, got {type(value)}")
                    result["valid"] = False
            
            elif key == "screenshot_timeout":
                try:
                    timeout = int(value)
                    if timeout < 100 or timeout > 30000:
                        result["issues"].append("screenshot_timeout must be between 100 and 30000")
                        result["valid"] = False
                    else:
                        sanitized[key] = timeout
                except (ValueError, TypeError):
                    result["issues"].append(f"screenshot_timeout must be integer, got {type(value)}")
                    result["valid"] = False
            
            else:
                result["warnings"].append(f"Unknown setting: {key}")
        
        result["sanitized_settings"] = sanitized
        
        # Additional validation warnings
        if sanitized["screenshot_format"] in ["jpeg", "jpg"] and sanitized["screenshot_quality"] < 30:
            result["warnings"].append("JPEG quality below 30 may produce poor results")
        
        if sanitized["screenshot_cleanup_hours"] < 1:
            result["warnings"].append("Very short cleanup interval may impact performance")
        
        return result
        
    except Exception as e:
        logger.error(f"Settings validation failed: {str(e)}")
        return {
            "valid": False,
            "issues": [f"Validation error: {str(e)}"],
            "warnings": [],
            "sanitized_settings": {}
        }

def validate_base_path(base_path: Union[str, Path]) -> bool:
    """
    Validate base path for screenshot storage
    
    Args:
        base_path: Base directory path to validate
        
    Returns:
        True if path is valid
        
    Raises:
        ValueError: If path is invalid
    """
    try:
        if isinstance(base_path, str):
            base_path = Path(base_path)
        
        # Check if path is absolute
        if not base_path.is_absolute():
            raise ValueError("Base path must be absolute")
        
        # Check path length
        if len(str(base_path)) > 200:  # Leave room for filenames
            raise ValueError("Base path too long")
        
        # Check for invalid characters
        invalid_chars = '<>:"|?*'
        if any(char in str(base_path) for char in invalid_chars):
            raise ValueError(f"Base path contains invalid characters: {invalid_chars}")
        
        # Try to create the directory to test permissions
        try:
            base_path.mkdir(parents=True, exist_ok=True)
            
            # Test write permissions
            test_file = base_path / ".test_write_permission"
            test_file.touch()
            test_file.unlink()
            
        except (OSError, PermissionError) as e:
            raise ValueError(f"Cannot create or write to base path: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Base path validation failed: {str(e)}")
        raise ValueError(f"Invalid base path: {str(e)}")

def create_validation_report(config: ScreenshotConfig, base_path: Path) -> Dict[str, Any]:
    """
    Create comprehensive validation report
    
    Args:
        config: Screenshot configuration
        base_path: Base directory path
        
    Returns:
        Validation report dictionary
    """
    report = {
        "timestamp": time.time(),
        "config_valid": False,
        "path_valid": False,
        "overall_valid": False,
        "config_issues": [],
        "path_issues": [],
        "warnings": [],
        "recommendations": []
    }
    
    try:
        # Validate configuration
        config_issues = validate_screenshot_config(config)
        report["config_issues"] = config_issues
        report["config_valid"] = len(config_issues) == 0
        
        # Validate base path
        try:
            validate_base_path(base_path)
            report["path_valid"] = True
        except ValueError as e:
            report["path_issues"].append(str(e))
            report["path_valid"] = False
        
        # Overall validation
        report["overall_valid"] = report["config_valid"] and report["path_valid"]
        
        # Generate recommendations
        if config.format in ["jpeg", "jpg"] and config.quality > 95:
            report["recommendations"].append("Consider lowering JPEG quality to reduce file size")
        
        if config.timeout > 10000:
            report["recommendations"].append("Long timeout may cause delays in screenshot capture")
        
        if config.full_page:
            report["recommendations"].append("Full page screenshots may be large and slow")
        
        return report
        
    except Exception as e:
        logger.error(f"Validation report generation failed: {str(e)}")
        report["config_issues"].append(f"Validation error: {str(e)}")
        return report