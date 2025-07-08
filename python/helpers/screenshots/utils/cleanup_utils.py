"""
Cleanup utilities for screenshot management
"""

import asyncio
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

async def cleanup_old_screenshots(
    base_path: Path, 
    max_age_hours: int = 24,
    max_files: Optional[int] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Remove screenshots older than max_age_hours with comprehensive reporting
    
    Args:
        base_path: Base directory to clean
        max_age_hours: Maximum age in hours before cleanup
        max_files: Maximum number of files to keep (newest first)
        dry_run: If True, only report what would be cleaned
        
    Returns:
        Dictionary with cleanup results
    """
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    
    if not base_path.exists():
        logger.info(f"Base path {base_path} does not exist, nothing to clean")
        return {
            "cleaned_files": [],
            "kept_files": [],
            "errors": [],
            "total_cleaned": 0,
            "total_kept": 0,
            "space_freed": 0,
            "dry_run": dry_run
        }
    
    cutoff_time = time.time() - (max_age_hours * 3600)
    cleaned_files = []
    kept_files = []
    errors = []
    space_freed = 0
    
    try:
        # Get all screenshot files
        screenshot_files = []
        for pattern in ["*.png", "*.jpg", "*.jpeg"]:
            screenshot_files.extend(base_path.glob(pattern))
        
        # Sort by modification time (newest first)
        screenshot_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Apply max_files limit first
        if max_files and len(screenshot_files) > max_files:
            files_to_remove = screenshot_files[max_files:]
            files_to_keep = screenshot_files[:max_files]
            
            for file_path in files_to_remove:
                try:
                    file_info = {
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "age_hours": round((time.time() - file_path.stat().st_mtime) / 3600, 2),
                        "reason": "exceeded_max_files"
                    }
                    
                    if not dry_run:
                        space_freed += file_path.stat().st_size
                        file_path.unlink()
                    
                    cleaned_files.append(file_info)
                    
                except Exception as e:
                    errors.append({
                        "path": str(file_path),
                        "error": str(e),
                        "operation": "max_files_cleanup"
                    })
            
            screenshot_files = files_to_keep
        
        # Apply age-based cleanup
        for file_path in screenshot_files:
            try:
                file_stat = file_path.stat()
                file_age_hours = (time.time() - file_stat.st_mtime) / 3600
                
                file_info = {
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "age_hours": round(file_age_hours, 2)
                }
                
                if file_stat.st_mtime < cutoff_time:
                    # File is old, remove it
                    file_info["reason"] = "exceeded_age_limit"
                    
                    if not dry_run:
                        space_freed += file_stat.st_size
                        file_path.unlink()
                    
                    cleaned_files.append(file_info)
                else:
                    # File is recent, keep it
                    kept_files.append(file_info)
                    
            except Exception as e:
                errors.append({
                    "path": str(file_path),
                    "error": str(e),
                    "operation": "age_cleanup"
                })
        
        # Clean up empty directories
        if not dry_run:
            await cleanup_empty_directories(base_path)
        
        result = {
            "cleaned_files": cleaned_files,
            "kept_files": kept_files,
            "errors": errors,
            "total_cleaned": len(cleaned_files),
            "total_kept": len(kept_files),
            "space_freed": space_freed,
            "space_freed_mb": round(space_freed / (1024 * 1024), 2),
            "dry_run": dry_run
        }
        
        if cleaned_files:
            logger.info(f"Cleaned up {len(cleaned_files)} screenshots, freed {result['space_freed_mb']} MB")
        
        return result
        
    except Exception as e:
        logger.error(f"Error during screenshot cleanup: {str(e)}")
        return {
            "cleaned_files": cleaned_files,
            "kept_files": kept_files,
            "errors": [{"error": str(e), "operation": "cleanup"}],
            "total_cleaned": len(cleaned_files),
            "total_kept": len(kept_files),
            "space_freed": space_freed,
            "dry_run": dry_run
        }

async def cleanup_empty_directories(base_path: Path) -> List[str]:
    """
    Remove empty screenshot directories
    
    Args:
        base_path: Base directory to check
        
    Returns:
        List of removed directory paths
    """
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    
    removed_directories = []
    
    try:
        # Walk through directory tree bottom-up
        for dir_path in sorted(base_path.rglob("*"), key=lambda x: len(x.parts), reverse=True):
            if dir_path.is_dir() and dir_path != base_path:
                try:
                    # Check if directory is empty
                    if not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        removed_directories.append(str(dir_path))
                        logger.info(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    logger.warning(f"Could not remove directory {dir_path}: {str(e)}")
        
        return removed_directories
        
    except Exception as e:
        logger.error(f"Error cleaning empty directories: {str(e)}")
        return removed_directories

async def cleanup_corrupted_screenshots(base_path: Path) -> Dict[str, Any]:
    """
    Remove corrupted or invalid screenshot files
    
    Args:
        base_path: Base directory to check
        
    Returns:
        Dictionary with cleanup results
    """
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    
    if not base_path.exists():
        return {
            "corrupted_files": [],
            "valid_files": [],
            "errors": [],
            "total_corrupted": 0,
            "total_valid": 0
        }
    
    corrupted_files = []
    valid_files = []
    errors = []
    
    try:
        # Check all image files
        for pattern in ["*.png", "*.jpg", "*.jpeg"]:
            for file_path in base_path.glob(pattern):
                try:
                    file_stat = file_path.stat()
                    file_info = {
                        "path": str(file_path),
                        "size": file_stat.st_size
                    }
                    
                    # Check for obvious corruption signs
                    is_corrupted = False
                    corruption_reasons = []
                    
                    # Check file size
                    if file_stat.st_size == 0:
                        is_corrupted = True
                        corruption_reasons.append("empty_file")
                    elif file_stat.st_size < 100:  # Very small files are likely corrupted
                        is_corrupted = True
                        corruption_reasons.append("file_too_small")
                    elif file_stat.st_size > 100 * 1024 * 1024:  # 100MB limit
                        is_corrupted = True
                        corruption_reasons.append("file_too_large")
                    
                    # Try to read first few bytes to check magic numbers
                    try:
                        with open(file_path, 'rb') as f:
                            header = f.read(10)
                            
                            # Check PNG magic number
                            if file_path.suffix.lower() == '.png':
                                if not header.startswith(b'\x89PNG\r\n\x1a\n'):
                                    is_corrupted = True
                                    corruption_reasons.append("invalid_png_header")
                            
                            # Check JPEG magic number
                            elif file_path.suffix.lower() in ['.jpg', '.jpeg']:
                                if not header.startswith(b'\xff\xd8\xff'):
                                    is_corrupted = True
                                    corruption_reasons.append("invalid_jpeg_header")
                                    
                    except Exception:
                        is_corrupted = True
                        corruption_reasons.append("unreadable_file")
                    
                    if is_corrupted:
                        file_info["corruption_reasons"] = corruption_reasons
                        try:
                            file_path.unlink()
                            corrupted_files.append(file_info)
                            logger.warning(f"Removed corrupted screenshot: {file_path}")
                        except Exception as e:
                            errors.append({
                                "path": str(file_path),
                                "error": str(e),
                                "operation": "remove_corrupted"
                            })
                    else:
                        valid_files.append(file_info)
                        
                except Exception as e:
                    errors.append({
                        "path": str(file_path),
                        "error": str(e),
                        "operation": "corruption_check"
                    })
        
        result = {
            "corrupted_files": corrupted_files,
            "valid_files": valid_files,
            "errors": errors,
            "total_corrupted": len(corrupted_files),
            "total_valid": len(valid_files)
        }
        
        if corrupted_files:
            logger.info(f"Removed {len(corrupted_files)} corrupted screenshots")
        
        return result
        
    except Exception as e:
        logger.error(f"Error during corruption cleanup: {str(e)}")
        return {
            "corrupted_files": corrupted_files,
            "valid_files": valid_files,
            "errors": [{"error": str(e), "operation": "corruption_cleanup"}],
            "total_corrupted": len(corrupted_files),
            "total_valid": len(valid_files)
        }

async def get_cleanup_statistics(base_path: Path) -> Dict[str, Any]:
    """
    Get statistics about screenshot files for cleanup planning
    
    Args:
        base_path: Base directory to analyze
        
    Returns:
        Dictionary with statistics
    """
    if not isinstance(base_path, Path):
        base_path = Path(base_path)
    
    if not base_path.exists():
        return {
            "total_files": 0,
            "total_size": 0,
            "by_age": {},
            "by_format": {},
            "oldest_file": None,
            "newest_file": None,
            "average_size": 0
        }
    
    try:
        files = []
        total_size = 0
        by_format = {}
        
        # Collect all screenshot files
        for pattern in ["*.png", "*.jpg", "*.jpeg"]:
            for file_path in base_path.glob(pattern):
                try:
                    file_stat = file_path.stat()
                    file_info = {
                        "path": file_path,
                        "size": file_stat.st_size,
                        "mtime": file_stat.st_mtime,
                        "format": file_path.suffix.lower()[1:]
                    }
                    files.append(file_info)
                    total_size += file_stat.st_size
                    
                    # Count by format
                    format_key = file_info["format"]
                    if format_key not in by_format:
                        by_format[format_key] = {"count": 0, "size": 0}
                    by_format[format_key]["count"] += 1
                    by_format[format_key]["size"] += file_stat.st_size
                    
                except Exception as e:
                    logger.warning(f"Could not analyze file {file_path}: {str(e)}")
        
        if not files:
            return {
                "total_files": 0,
                "total_size": 0,
                "by_age": {},
                "by_format": {},
                "oldest_file": None,
                "newest_file": None,
                "average_size": 0
            }
        
        # Sort by modification time
        files.sort(key=lambda x: x["mtime"])
        
        # Calculate age statistics
        current_time = time.time()
        by_age = {
            "last_hour": 0,
            "last_day": 0,
            "last_week": 0,
            "last_month": 0,
            "older": 0
        }
        
        for file_info in files:
            age_hours = (current_time - file_info["mtime"]) / 3600
            
            if age_hours < 1:
                by_age["last_hour"] += 1
            elif age_hours < 24:
                by_age["last_day"] += 1
            elif age_hours < 168:  # 7 days
                by_age["last_week"] += 1
            elif age_hours < 720:  # 30 days
                by_age["last_month"] += 1
            else:
                by_age["older"] += 1
        
        return {
            "total_files": len(files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_age": by_age,
            "by_format": by_format,
            "oldest_file": {
                "path": str(files[0]["path"]),
                "age_hours": round((current_time - files[0]["mtime"]) / 3600, 2)
            },
            "newest_file": {
                "path": str(files[-1]["path"]),
                "age_hours": round((current_time - files[-1]["mtime"]) / 3600, 2)
            },
            "average_size": round(total_size / len(files), 2),
            "average_size_mb": round(total_size / len(files) / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"Error getting cleanup statistics: {str(e)}")
        return {
            "total_files": 0,
            "total_size": 0,
            "by_age": {},
            "by_format": {},
            "oldest_file": None,
            "newest_file": None,
            "average_size": 0,
            "error": str(e)
        }