"""
File storage implementation for screenshots
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import time
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class StorageProvider(ABC):
    """Abstract base class for storage providers"""
    
    @abstractmethod
    async def store_screenshot(self, path: Path, metadata: Dict[str, Any]) -> bool:
        """Store screenshot with metadata"""
        pass
    
    @abstractmethod
    async def retrieve_screenshot(self, identifier: str) -> Optional[Path]:
        """Retrieve screenshot by identifier"""
        pass
    
    @abstractmethod
    async def delete_screenshot(self, identifier: str) -> bool:
        """Delete screenshot by identifier"""
        pass
    
    @abstractmethod
    async def list_screenshots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List stored screenshots"""
        pass

class FileStorage(StorageProvider):
    """
    File system storage provider for screenshots
    Manages screenshot files and metadata on local filesystem
    """
    
    def __init__(self, base_path: Path, create_metadata: bool = True):
        """
        Initialize file storage
        
        Args:
            base_path: Base directory for storage
            create_metadata: Whether to create metadata files
        """
        self.base_path = Path(base_path)
        self.create_metadata = create_metadata
        self.metadata_dir = self.base_path / ".metadata"
        
        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        if self.create_metadata:
            self.metadata_dir.mkdir(parents=True, exist_ok=True)
    
    async def store_screenshot(self, path: Path, metadata: Dict[str, Any]) -> bool:
        """
        Store screenshot with metadata
        
        Args:
            path: Path to screenshot file
            metadata: Metadata to store
            
        Returns:
            True if storage successful
        """
        try:
            if not path.exists():
                logger.error(f"Screenshot file does not exist: {path}")
                return False
            
            # Generate identifier
            identifier = self._generate_identifier(path)
            
            # Store metadata if enabled
            if self.create_metadata:
                metadata_path = self.metadata_dir / f"{identifier}.json"
                
                # Add storage metadata
                storage_metadata = {
                    "stored_at": time.time(),
                    "original_path": str(path),
                    "identifier": identifier,
                    "file_size": path.stat().st_size,
                    "storage_provider": "file_storage"
                }
                
                # Combine metadata
                full_metadata = {**metadata, **storage_metadata}
                
                # Write metadata
                with open(metadata_path, 'w') as f:
                    json.dump(full_metadata, f, indent=2)
            
            logger.info(f"Screenshot stored: {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store screenshot: {str(e)}")
            return False
    
    async def retrieve_screenshot(self, identifier: str) -> Optional[Path]:
        """
        Retrieve screenshot by identifier
        
        Args:
            identifier: Screenshot identifier
            
        Returns:
            Path to screenshot file or None if not found
        """
        try:
            # Look for file with identifier
            for ext in ['.png', '.jpg', '.jpeg']:
                screenshot_path = self.base_path / f"{identifier}{ext}"
                if screenshot_path.exists():
                    return screenshot_path
            
            # Look in metadata for original path
            if self.create_metadata:
                metadata_path = self.metadata_dir / f"{identifier}.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    original_path = Path(metadata.get("original_path", ""))
                    if original_path.exists():
                        return original_path
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve screenshot {identifier}: {str(e)}")
            return None
    
    async def delete_screenshot(self, identifier: str) -> bool:
        """
        Delete screenshot by identifier
        
        Args:
            identifier: Screenshot identifier
            
        Returns:
            True if deletion successful
        """
        try:
            deleted = False
            
            # Delete screenshot file
            screenshot_path = await self.retrieve_screenshot(identifier)
            if screenshot_path and screenshot_path.exists():
                screenshot_path.unlink()
                deleted = True
            
            # Delete metadata file
            if self.create_metadata:
                metadata_path = self.metadata_dir / f"{identifier}.json"
                if metadata_path.exists():
                    metadata_path.unlink()
                    deleted = True
            
            if deleted:
                logger.info(f"Screenshot deleted: {identifier}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Failed to delete screenshot {identifier}: {str(e)}")
            return False
    
    async def list_screenshots(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List stored screenshots
        
        Args:
            limit: Maximum number of screenshots to return
            
        Returns:
            List of screenshot information
        """
        try:
            screenshots = []
            
            # Get all screenshot files
            for ext in ['.png', '.jpg', '.jpeg']:
                for file_path in self.base_path.glob(f"*{ext}"):
                    if file_path.is_file():
                        identifier = self._generate_identifier(file_path)
                        
                        # Get basic file info
                        file_stat = file_path.stat()
                        screenshot_info = {
                            "identifier": identifier,
                            "path": str(file_path),
                            "size": file_stat.st_size,
                            "created": file_stat.st_ctime,
                            "modified": file_stat.st_mtime,
                            "format": ext[1:]  # Remove dot
                        }
                        
                        # Add metadata if available
                        if self.create_metadata:
                            metadata_path = self.metadata_dir / f"{identifier}.json"
                            if metadata_path.exists():
                                try:
                                    with open(metadata_path, 'r') as f:
                                        metadata = json.load(f)
                                    screenshot_info["metadata"] = metadata
                                except Exception as e:
                                    logger.warning(f"Failed to read metadata for {identifier}: {str(e)}")
                        
                        screenshots.append(screenshot_info)
            
            # Sort by creation time (newest first)
            screenshots.sort(key=lambda x: x["created"], reverse=True)
            
            # Apply limit
            return screenshots[:limit]
            
        except Exception as e:
            logger.error(f"Failed to list screenshots: {str(e)}")
            return []
    
    async def get_metadata(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for screenshot
        
        Args:
            identifier: Screenshot identifier
            
        Returns:
            Metadata dictionary or None if not found
        """
        try:
            if not self.create_metadata:
                return None
            
            metadata_path = self.metadata_dir / f"{identifier}.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get metadata for {identifier}: {str(e)}")
            return None
    
    async def update_metadata(self, identifier: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for screenshot
        
        Args:
            identifier: Screenshot identifier
            metadata: New metadata to merge
            
        Returns:
            True if update successful
        """
        try:
            if not self.create_metadata:
                return False
            
            metadata_path = self.metadata_dir / f"{identifier}.json"
            
            # Get existing metadata
            existing_metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    existing_metadata = json.load(f)
            
            # Merge metadata
            existing_metadata.update(metadata)
            existing_metadata["updated_at"] = time.time()
            
            # Write updated metadata
            with open(metadata_path, 'w') as f:
                json.dump(existing_metadata, f, indent=2)
            
            logger.info(f"Metadata updated for {identifier}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metadata for {identifier}: {str(e)}")
            return False
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            screenshots = await self.list_screenshots(limit=10000)  # Get all
            
            total_size = sum(s["size"] for s in screenshots)
            
            # Group by format
            by_format = {}
            for screenshot in screenshots:
                format_key = screenshot["format"]
                if format_key not in by_format:
                    by_format[format_key] = {"count": 0, "size": 0}
                by_format[format_key]["count"] += 1
                by_format[format_key]["size"] += screenshot["size"]
            
            # Calculate age distribution
            current_time = time.time()
            age_distribution = {
                "last_hour": 0,
                "last_day": 0,
                "last_week": 0,
                "last_month": 0,
                "older": 0
            }
            
            for screenshot in screenshots:
                age_hours = (current_time - screenshot["created"]) / 3600
                
                if age_hours < 1:
                    age_distribution["last_hour"] += 1
                elif age_hours < 24:
                    age_distribution["last_day"] += 1
                elif age_hours < 168:  # 7 days
                    age_distribution["last_week"] += 1
                elif age_hours < 720:  # 30 days
                    age_distribution["last_month"] += 1
                else:
                    age_distribution["older"] += 1
            
            return {
                "total_screenshots": len(screenshots),
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "by_format": by_format,
                "age_distribution": age_distribution,
                "storage_path": str(self.base_path),
                "metadata_enabled": self.create_metadata,
                "oldest_screenshot": min(screenshots, key=lambda x: x["created"])["created"] if screenshots else None,
                "newest_screenshot": max(screenshots, key=lambda x: x["created"])["created"] if screenshots else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage statistics: {str(e)}")
            return {"error": str(e)}
    
    def _generate_identifier(self, path: Path) -> str:
        """
        Generate identifier from file path
        
        Args:
            path: File path
            
        Returns:
            Unique identifier
        """
        return path.stem  # Use filename without extension as identifier
    
    async def cleanup_orphaned_metadata(self) -> int:
        """
        Clean up metadata files without corresponding screenshots
        
        Returns:
            Number of orphaned metadata files removed
        """
        if not self.create_metadata:
            return 0
        
        try:
            removed_count = 0
            
            for metadata_file in self.metadata_dir.glob("*.json"):
                identifier = metadata_file.stem
                screenshot_path = await self.retrieve_screenshot(identifier)
                
                if screenshot_path is None or not screenshot_path.exists():
                    metadata_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed orphaned metadata: {identifier}")
            
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned metadata: {str(e)}")
            return 0