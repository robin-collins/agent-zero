"""
Migration script to safely replace browser_agent.py with enhanced version
"""

import shutil
import os
import time
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def migrate_browser_agent():
    """
    Migrate from original browser_agent.py to enhanced version
    """
    base_path = Path(__file__).parent
    original_file = base_path / "browser_agent.py"
    enhanced_file = base_path / "browser_agent_enhanced.py"
    backup_file = base_path / f"browser_agent_backup_{int(time.time())}.py"
    
    try:
        # Step 1: Backup original file
        if original_file.exists():
            shutil.copy2(original_file, backup_file)
            logger.info(f"Backed up original browser_agent.py to {backup_file}")
        
        # Step 2: Verify enhanced file exists
        if not enhanced_file.exists():
            logger.error("Enhanced browser_agent_enhanced.py not found!")
            return False
        
        # Step 3: Replace original with enhanced version
        shutil.copy2(enhanced_file, original_file)
        logger.info("Replaced browser_agent.py with enhanced version")
        
        # Step 4: Verify the replacement
        if original_file.exists():
            logger.info("Migration completed successfully")
            return True
        else:
            logger.error("Migration failed - original file not found after replacement")
            return False
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        
        # Try to restore backup if migration failed
        if backup_file.exists():
            try:
                shutil.copy2(backup_file, original_file)
                logger.info("Restored original browser_agent.py from backup")
            except Exception as restore_e:
                logger.error(f"Failed to restore backup: {str(restore_e)}")
        
        return False

def rollback_browser_agent():
    """
    Rollback to most recent backup
    """
    base_path = Path(__file__).parent
    original_file = base_path / "browser_agent.py"
    
    # Find most recent backup
    backup_files = list(base_path.glob("browser_agent_backup_*.py"))
    if not backup_files:
        logger.error("No backup files found!")
        return False
    
    # Get most recent backup
    latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)
    
    try:
        shutil.copy2(latest_backup, original_file)
        logger.info(f"Rolled back to {latest_backup}")
        return True
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_browser_agent()