"""
Path utilities for screenshot management
"""

from pathlib import Path
import uuid
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def generate_screenshot_path(base_path: Path, format: str = "png", prefix: str = "") -> Path:
    """
    Generate unique screenshot path with timestamp and UUID
    
    Args:
        base_path: Base directory for screenshots
        format: File format (png, jpeg, jpg)
        prefix: Optional prefix for filename
        
    Returns:
        Path object for screenshot file
    """
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    
    # Validate format
    if format not in ["png", "jpeg", "jpg"]:
        logger.warning(f"Invalid format '{format}', defaulting to 'png'")
        format = "png"
    
    # Generate unique filename
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID
    
    if prefix:
        filename = f"{prefix}_{timestamp}_{unique_id}.{format}"
    else:
        filename = f"screenshot_{timestamp}_{unique_id}.{format}"
    
    return base_path / filename

def ensure_screenshot_directory(path: Path) -> bool:
    """
    Ensure screenshot directory exists with proper permissions
    
    Args:
        path: Directory path to create
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        if not isinstance(path, Path):
            path = Path(path)
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Verify directory is writable
        test_file = path / ".test_write"
        try:
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            logger.error(f"Directory {path} is not writable")
            return False
            
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {str(e)}")
        return False

def get_screenshot_info(path: Path) -> Optional[Dict[str, Any]]:
    """
    Get screenshot file information and metadata
    
    Args:
        path: Path to screenshot file
        
    Returns:
        Dictionary with file information or None if file doesn't exist
    """
    try:
        if not isinstance(path, Path):
            path = Path(path)
        
        if not path.exists():
            return None
        
        if not path.is_file():
            logger.warning(f"Path {path} is not a file")
            return None
        
        stat = path.stat()
        
        # Extract format from extension
        format_ext = path.suffix.lower()[1:] if path.suffix else "unknown"
        
        # Calculate age
        age_seconds = time.time() - stat.st_mtime
        
        return {
            "path": str(path),
            "filename": path.name,
            "size": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "format": format_ext,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "age_seconds": int(age_seconds),
            "age_hours": round(age_seconds / 3600, 2),
            "is_recent": age_seconds < 3600,  # Less than 1 hour old
            "permissions": oct(stat.st_mode)[-3:],
            "is_readable": path.is_file() and path.stat().st_mode & 0o444,
            "is_writable": path.is_file() and path.stat().st_mode & 0o222
        }
        
    except Exception as e:
        logger.error(f"Failed to get screenshot info for {path}: {str(e)}")
        return None

def normalize_screenshot_path(path: Path, base_path: Path) -> Path:
    """
    Normalize screenshot path to ensure it's within base directory
    
    Args:
        path: Path to normalize
        base_path: Base directory for screenshots
        
    Returns:
        Normalized path within base directory
    """
    try:
        if not isinstance(path, Path):
            path = Path(path)
        if not isinstance(base_path, Path):
            base_path = Path(base_path)
        
        # Resolve any relative components
        path = path.resolve()
        base_path = base_path.resolve()
        
        # Ensure path is within base directory
        try:
            path.relative_to(base_path)
            return path
        except ValueError:
            # Path is outside base directory, create safe path
            logger.warning(f"Path {path} is outside base directory {base_path}")
            return generate_screenshot_path(base_path, format="png", prefix="normalized")
            
    except Exception as e:
        logger.error(f"Failed to normalize path {path}: {str(e)}")
        return generate_screenshot_path(base_path, format="png", prefix="error")

def is_screenshot_file(path: Path) -> bool:
    """
    Check if file is a valid screenshot file
    
    Args:
        path: Path to check
        
    Returns:
        True if file appears to be a screenshot
    """
    try:
        if not isinstance(path, Path):
            path = Path(path)
        
        if not path.exists() or not path.is_file():
            return False
        
        # Check file extension
        valid_extensions = {".png", ".jpg", ".jpeg"}
        if path.suffix.lower() not in valid_extensions:
            return False
        
        # Check file size (screenshots shouldn't be empty or extremely large)
        file_size = path.stat().st_size
        if file_size == 0 or file_size > 100 * 1024 * 1024:  # 100MB limit
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to check if {path} is screenshot file: {str(e)}")
        return False