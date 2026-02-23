"""
Sync engine module
Handles file synchronization between local and cloud
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SyncAction(Enum):
    """Sync action types"""
    COPY_TO_CLOUD = "copy_to_cloud"
    COPY_TO_LOCAL = "copy_to_local"
    CONFLICT = "conflict"
    SKIP = "skip"


class FileComparison:
    """Represents a file comparison result"""
    
    def __init__(self, filename: str, local_path: Optional[Path], cloud_path: Optional[Path]):
        """Initialize file comparison
        
        Args:
            filename: Name of the file
            local_path: Path to local file (None if doesn't exist)
            cloud_path: Path to cloud file (None if doesn't exist)
        """
        self.filename = filename
        self.local_path = local_path
        self.cloud_path = cloud_path
        self.action = SyncAction.SKIP
        self.local_mtime: Optional[float] = None
        self.cloud_mtime: Optional[float] = None
        self.local_size: Optional[int] = None
        self.cloud_size: Optional[int] = None
        
        # Get file stats
        if local_path and local_path.exists():
            stat = local_path.stat()
            self.local_mtime = stat.st_mtime
            self.local_size = stat.st_size
        
        if cloud_path and cloud_path.exists():
            stat = cloud_path.stat()
            self.cloud_mtime = stat.st_mtime
            self.cloud_size = stat.st_size
    
    def __repr__(self):
        return f"FileComparison({self.filename}, action={self.action.value})"


class SyncEngine:
    """Handles file synchronization operations"""
    
    def __init__(self):
        """Initialize sync engine"""
        pass
    
    def compare_directories(self, local_dir: Path, cloud_dir: Path, last_sync: Optional[str] = None) -> List[FileComparison]:
        """Compare files in local and cloud directories
        
        Args:
            local_dir: Local directory path
            cloud_dir: Cloud directory path
            last_sync: ISO format timestamp of last sync (optional)
            
        Returns:
            List of FileComparison objects
        """
        comparisons = []
        
        # Convert last_sync to timestamp
        last_sync_time = None
        if last_sync:
            try:
                dt = datetime.fromisoformat(last_sync)
                last_sync_time = dt.timestamp()
            except:
                pass
        
        # Get all files from both directories
        local_files = self._get_files(local_dir) if local_dir.exists() else set()
        cloud_files = self._get_files(cloud_dir) if cloud_dir.exists() else set()
        all_files = local_files | cloud_files
        
        for filename in sorted(all_files):
            local_path = local_dir / filename if filename in local_files else None
            cloud_path = cloud_dir / filename if filename in cloud_files else None
            
            comparison = FileComparison(filename, local_path, cloud_path)
            comparison.action = self._determine_action(comparison, last_sync_time)
            comparisons.append(comparison)
        
        return comparisons
    
    def _get_files(self, directory: Path) -> set:
        """Get all files in directory (non-recursive)
        
        Args:
            directory: Directory to scan
            
        Returns:
            Set of filenames
        """
        if not directory.exists():
            return set()
        
        files = set()
        try:
            for item in directory.iterdir():
                if item.is_file():
                    files.add(item.name)
        except PermissionError:
            pass
        
        return files
    
    def _determine_action(self, comparison: FileComparison, last_sync_time: Optional[float]) -> SyncAction:
        """Determine what action to take for a file
        
        Args:
            comparison: FileComparison object
            last_sync_time: Timestamp of last sync (optional)
            
        Returns:
            SyncAction to take
        """
        local_exists = comparison.local_path and comparison.local_path.exists()
        cloud_exists = comparison.cloud_path and comparison.cloud_path.exists()
        
        # File only exists locally
        if local_exists and not cloud_exists:
            return SyncAction.COPY_TO_CLOUD
        
        # File only exists in cloud
        if cloud_exists and not local_exists:
            return SyncAction.COPY_TO_LOCAL
        
        # File exists in both locations
        if local_exists and cloud_exists:
            # Compare timestamps
            local_mtime = comparison.local_mtime
            cloud_mtime = comparison.cloud_mtime
            
            # If we have last_sync_time, check for conflicts
            if last_sync_time:
                local_modified = local_mtime > last_sync_time
                cloud_modified = cloud_mtime > last_sync_time
                
                # Both modified since last sync = conflict
                if local_modified and cloud_modified:
                    return SyncAction.CONFLICT
                
                # Only local modified
                if local_modified and not cloud_modified:
                    return SyncAction.COPY_TO_CLOUD
                
                # Only cloud modified
                if cloud_modified and not local_modified:
                    return SyncAction.COPY_TO_LOCAL
                
                # Neither modified
                return SyncAction.SKIP
            
            # No last_sync_time, use simple timestamp comparison
            if local_mtime > cloud_mtime:
                return SyncAction.COPY_TO_CLOUD
            elif cloud_mtime > local_mtime:
                return SyncAction.COPY_TO_LOCAL
            else:
                return SyncAction.SKIP
        
        return SyncAction.SKIP
    
    def copy_file(self, source: Path, dest: Path, preserve_timestamp: bool = True) -> bool:
        """Copy file from source to destination
        
        Args:
            source: Source file path
            dest: Destination file path
            preserve_timestamp: Preserve file modification time (default: True)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure destination directory exists
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(source, dest) if preserve_timestamp else shutil.copy(source, dest)
            
            # Get typical permissions from destination directory
            # This handles cloud storage that may not preserve permissions
            try:
                # Try to match permissions of other files in the directory
                if dest.parent.exists():
                    for sibling in dest.parent.iterdir():
                        if sibling.is_file() and sibling != dest:
                            # Copy permissions from existing file
                            sibling_stat = sibling.stat()
                            os.chmod(dest, sibling_stat.st_mode)
                            break
                    else:
                        # No other files, use safe default (rw-r--r--)
                        os.chmod(dest, 0o644)
            except (OSError, PermissionError):
                # If we can't set permissions, that's okay
                # Cloud storage might handle this differently
                pass
            
            return True
            
        except Exception as e:
            print(f"Error copying {source} to {dest}: {e}")
            return False
    
    def verify_disk_space(self, dest_dir: Path, required_bytes: int) -> bool:
        """Verify sufficient disk space is available
        
        Args:
            dest_dir: Destination directory
            required_bytes: Required space in bytes
            
        Returns:
            True if sufficient space available
        """
        try:
            stat = os.statvfs(dest_dir)
            available = stat.f_bavail * stat.f_frsize
            return available >= required_bytes
        except:
            # If we can't check, assume it's okay
            return True
    
    def get_sync_summary(self, comparisons: List[FileComparison]) -> Dict[str, Any]:
        """Get summary of sync actions
        
        Args:
            comparisons: List of FileComparison objects
            
        Returns:
            Dictionary with counts of each action
        """
        summary = {
            "total_files": len(comparisons),
            "copy_to_cloud": 0,
            "copy_to_local": 0,
            "conflicts": 0,
            "skip": 0,
            "files": {
                "copy_to_cloud": [],
                "copy_to_local": [],
                "conflicts": [],
                "skip": []
            }
        }
        
        for comp in comparisons:
            if comp.action == SyncAction.COPY_TO_CLOUD:
                summary["copy_to_cloud"] += 1
                summary["files"]["copy_to_cloud"].append(comp.filename)
            elif comp.action == SyncAction.COPY_TO_LOCAL:
                summary["copy_to_local"] += 1
                summary["files"]["copy_to_local"].append(comp.filename)
            elif comp.action == SyncAction.CONFLICT:
                summary["conflicts"] += 1
                summary["files"]["conflicts"].append(comp.filename)
            else:
                summary["skip"] += 1
                summary["files"]["skip"].append(comp.filename)
        
        return summary
