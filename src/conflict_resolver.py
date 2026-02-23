"""Conflict resolution for game save synchronization"""

from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    KEEP_LOCAL = "keep_local"
    KEEP_CLOUD = "keep_cloud"
    KEEP_BOTH = "keep_both"
    MANUAL = "manual"


class ConflictResolver:
    """Handles conflict detection and resolution"""
    
    def __init__(self):
        self.pending_conflicts = []
    
    def add_conflict(self, local_path: Path, cloud_path: Path):
        """Add a conflict to the pending list
        
        Args:
            local_path: Path to local file
            cloud_path: Path to cloud file
        """
        conflict = {
            "filename": local_path.name,
            "local_path": str(local_path),
            "cloud_path": str(cloud_path),
            "detected_at": datetime.now().isoformat()
        }
        self.pending_conflicts.append(conflict)
    
    def list_conflicts(self) -> list:
        """List all pending conflicts
        
        Returns:
            List of conflict dictionaries
        """
        return self.pending_conflicts.copy()
    
    def clear_conflicts(self):
        """Clear all pending conflicts"""
        self.pending_conflicts.clear()
    
    def detect_conflict(self, local_path: Path, cloud_path: Path, 
                       last_sync: Optional[str] = None) -> bool:
        """Detect if files are in conflict
        
        Args:
            local_path: Path to local file
            cloud_path: Path to cloud file
            last_sync: ISO format timestamp of last sync
            
        Returns:
            True if conflict detected
        """
        if not local_path.exists() or not cloud_path.exists():
            return False
        
        local_mtime = local_path.stat().st_mtime
        cloud_mtime = cloud_path.stat().st_mtime
        
        # If no last sync, check if both modified at different times
        if not last_sync:
            # Allow 2 second tolerance for filesystem timestamp precision
            return abs(local_mtime - cloud_mtime) > 2
        
        # Parse last sync timestamp
        last_sync_dt = datetime.fromisoformat(last_sync)
        last_sync_ts = last_sync_dt.timestamp()
        
        # Conflict if both modified after last sync
        local_newer = local_mtime > last_sync_ts + 1
        cloud_newer = cloud_mtime > last_sync_ts + 1
        
        return local_newer and cloud_newer
    
    def create_conflict_backup(self, local_path: Path, cloud_path: Path, 
                              backup_dir: Path) -> Dict[str, Path]:
        """Create backups of both conflicting versions
        
        Args:
            local_path: Path to local file
            cloud_path: Path to cloud file
            backup_dir: Directory for backups
            
        Returns:
            Dictionary with backup paths
        """
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = local_path.name
        
        backups = {}
        
        # Backup local version
        if local_path.exists():
            local_backup = backup_dir / f"{filename}.{timestamp}.local.conflict"
            local_backup.write_bytes(local_path.read_bytes())
            backups["local"] = local_backup
        
        # Backup cloud version
        if cloud_path.exists():
            cloud_backup = backup_dir / f"{filename}.{timestamp}.cloud.conflict"
            cloud_backup.write_bytes(cloud_path.read_bytes())
            backups["cloud"] = cloud_backup
        
        return backups
    
    def get_conflict_info(self, local_path: Path, cloud_path: Path) -> Dict[str, Any]:
        """Get detailed information about conflicting files
        
        Args:
            local_path: Path to local file
            cloud_path: Path to cloud file
            
        Returns:
            Dictionary with conflict details
        """
        info = {
            "filename": local_path.name,
            "local": {},
            "cloud": {}
        }
        
        if local_path.exists():
            stat = local_path.stat()
            info["local"] = {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(local_path)
            }
        
        if cloud_path.exists():
            stat = cloud_path.stat()
            info["cloud"] = {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": str(cloud_path)
            }
        
        return info
    
    def resolve_conflict(self, local_path: Path, cloud_path: Path, 
                        strategy: ResolutionStrategy, backup_dir: Path) -> bool:
        """Resolve conflict using specified strategy
        
        Args:
            local_path: Path to local file
            cloud_path: Path to cloud file
            strategy: Resolution strategy to apply
            backup_dir: Directory for backups
            
        Returns:
            True if resolution successful
        """
        # Create backups first
        self.create_conflict_backup(local_path, cloud_path, backup_dir)
        
        if strategy == ResolutionStrategy.KEEP_LOCAL:
            # Copy local to cloud
            cloud_path.write_bytes(local_path.read_bytes())
            cloud_path.touch()  # Update timestamp
            return True
        
        elif strategy == ResolutionStrategy.KEEP_CLOUD:
            # Copy cloud to local
            local_path.write_bytes(cloud_path.read_bytes())
            local_path.touch()  # Update timestamp
            return True
        
        elif strategy == ResolutionStrategy.KEEP_BOTH:
            # Rename both with suffixes
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            
            # Rename local
            local_new = local_path.parent / f"{local_path.stem}.{timestamp}.local{local_path.suffix}"
            local_path.rename(local_new)
            
            # Rename cloud
            cloud_new = cloud_path.parent / f"{cloud_path.stem}.{timestamp}.cloud{cloud_path.suffix}"
            cloud_path.rename(cloud_new)
            
            return True
        
        return False
