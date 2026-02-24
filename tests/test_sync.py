#!/usr/bin/env python3
"""
Test script for sync engine
"""

import sys
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sync_engine import SyncEngine, SyncAction


def test_file_only_local():
    """Test file exists only locally"""
    print("Test 1: File exists only locally...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create file only in local
        (local_dir / "save.dat").write_text("local data")
        
        engine = SyncEngine()
        comparisons = engine.compare_directories(local_dir, cloud_dir)
        
        assert len(comparisons) == 1
        assert comparisons[0].action == SyncAction.COPY_TO_CLOUD
        print("  ✓ Correctly identified: copy to cloud")
        return True


def test_file_only_cloud():
    """Test file exists only in cloud"""
    print("\nTest 2: File exists only in cloud...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create file only in cloud
        (cloud_dir / "save.dat").write_text("cloud data")
        
        engine = SyncEngine()
        comparisons = engine.compare_directories(local_dir, cloud_dir)
        
        assert len(comparisons) == 1
        assert comparisons[0].action == SyncAction.COPY_TO_LOCAL
        print("  ✓ Correctly identified: copy to local")
        return True


def test_local_newer():
    """Test local file is newer"""
    print("\nTest 3: Local file is newer...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create cloud file first
        cloud_file = cloud_dir / "save.dat"
        cloud_file.write_text("cloud data")
        
        time.sleep(0.1)
        
        # Create local file (newer)
        local_file = local_dir / "save.dat"
        local_file.write_text("local data")
        
        engine = SyncEngine()
        comparisons = engine.compare_directories(local_dir, cloud_dir)
        
        assert len(comparisons) == 1
        assert comparisons[0].action == SyncAction.COPY_TO_CLOUD
        print("  ✓ Correctly identified: copy to cloud (local newer)")
        return True


def test_cloud_newer():
    """Test cloud file is newer"""
    print("\nTest 4: Cloud file is newer...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create local file first
        local_file = local_dir / "save.dat"
        local_file.write_text("local data")
        
        time.sleep(0.1)
        
        # Create cloud file (newer)
        cloud_file = cloud_dir / "save.dat"
        cloud_file.write_text("cloud data")
        
        engine = SyncEngine()
        comparisons = engine.compare_directories(local_dir, cloud_dir)
        
        assert len(comparisons) == 1
        assert comparisons[0].action == SyncAction.COPY_TO_LOCAL
        print("  ✓ Correctly identified: copy to local (cloud newer)")
        return True


def test_conflict_detection():
    """Test conflict detection with last_sync"""
    print("\nTest 5: Conflict detection...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create both files
        local_file = local_dir / "save.dat"
        cloud_file = cloud_dir / "save.dat"
        
        local_file.write_text("old data")
        cloud_file.write_text("old data")
        
        # Record sync time
        time.sleep(0.1)
        last_sync = datetime.now().isoformat()
        time.sleep(0.1)
        
        # Modify both files after sync
        local_file.write_text("local modified")
        time.sleep(0.1)
        cloud_file.write_text("cloud modified")
        
        engine = SyncEngine()
        comparisons = engine.compare_directories(local_dir, cloud_dir, last_sync)
        
        assert len(comparisons) == 1
        assert comparisons[0].action == SyncAction.CONFLICT
        print("  ✓ Correctly identified: conflict")
        return True


def test_sync_summary():
    """Test sync summary generation"""
    print("\nTest 6: Sync summary...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create various scenarios
        (local_dir / "only_local.dat").write_text("data")
        (cloud_dir / "only_cloud.dat").write_text("data")
        (local_dir / "same.dat").write_text("data")
        (cloud_dir / "same.dat").write_text("data")
        
        engine = SyncEngine()
        comparisons = engine.compare_directories(local_dir, cloud_dir)
        summary = engine.get_sync_summary(comparisons)
        
        print(f"  Total files: {summary['total_files']}")
        print(f"  Copy to cloud: {summary['copy_to_cloud']}")
        print(f"  Copy to local: {summary['copy_to_local']}")
        print(f"  Conflicts: {summary['conflicts']}")
        print(f"  Skip: {summary['skip']}")
        
        assert summary['total_files'] == 3
        assert summary['copy_to_cloud'] >= 1
        assert summary['copy_to_local'] >= 1
        print("  ✓ Summary generated correctly")
        return True


def test_copy_file():
    """Test file copying"""
    print("\nTest 7: File copying...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        dest_dir = Path(tmpdir) / "dest"
        source_dir.mkdir()
        
        # Create source file
        source_file = source_dir / "test.dat"
        source_file.write_text("test data")
        original_mtime = source_file.stat().st_mtime
        
        # Copy file
        dest_file = dest_dir / "test.dat"
        engine = SyncEngine()
        success = engine.copy_file(source_file, dest_file)
        
        assert success
        assert dest_file.exists()
        assert dest_file.read_text() == "test data"
        
        # Check timestamp preserved
        dest_mtime = dest_file.stat().st_mtime
        assert abs(dest_mtime - original_mtime) < 0.01
        
        print("  ✓ File copied successfully with timestamp preserved")
        return True


def test_copy_file_permissions():
    """Test file permission handling"""
    print("\nTest 8: File permission handling...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        source_dir = Path(tmpdir) / "source"
        dest_dir = Path(tmpdir) / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create existing file in dest with specific permissions
        existing_file = dest_dir / "existing.dat"
        existing_file.write_text("existing")
        os.chmod(existing_file, 0o644)
        
        # Create source file
        source_file = source_dir / "test.dat"
        source_file.write_text("test data")
        
        # Copy file
        dest_file = dest_dir / "test.dat"
        engine = SyncEngine()
        success = engine.copy_file(source_file, dest_file)
        
        assert success
        assert dest_file.exists()
        
        # Check permissions match existing file
        dest_mode = dest_file.stat().st_mode & 0o777
        existing_mode = existing_file.stat().st_mode & 0o777
        assert dest_mode == existing_mode
        
        print(f"  ✓ Permissions matched existing files: {oct(dest_mode)}")
        return True


def test_disk_space_check():
    """Test disk space verification"""
    print("\nTest 9: Disk space verification...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        dest_dir = Path(tmpdir)
        
        engine = SyncEngine()
        
        # Should have space for small file
        has_space = engine.verify_disk_space(dest_dir, 1024)
        assert has_space
        print("  ✓ Disk space check works")
        return True


def test_create_backup():
    """Test backup creation"""
    print("\nTest 10: Backup creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_dir = Path(tmpdir) / "files"
        backup_dir = Path(tmpdir) / "backups"
        file_dir.mkdir()
        
        # Create file to backup
        test_file = file_dir / "save.dat"
        test_file.write_text("important data")
        
        engine = SyncEngine()
        backup_path = engine.create_backup(test_file, backup_dir, "local")
        
        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.read_text() == "important data"
        
        # Check backup filename format
        assert "save.dat" in backup_path.name
        assert ".local.backup" in backup_path.name
        
        print(f"  ✓ Backup created: {backup_path.name}")
        return True


def test_backup_with_timestamp():
    """Test backup timestamp uniqueness"""
    print("\nTest 11: Backup timestamp uniqueness...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_dir = Path(tmpdir) / "files"
        backup_dir = Path(tmpdir) / "backups"
        file_dir.mkdir()
        
        # Create file
        test_file = file_dir / "save.dat"
        test_file.write_text("data v1")
        
        engine = SyncEngine()
        
        # Create first backup
        backup1 = engine.create_backup(test_file, backup_dir, "local")
        
        time.sleep(1.1)  # Ensure different timestamp
        
        # Modify and create second backup
        test_file.write_text("data v2")
        backup2 = engine.create_backup(test_file, backup_dir, "cloud")
        
        assert backup1 != backup2
        assert backup1.exists()
        assert backup2.exists()
        assert backup1.read_text() == "data v1"
        assert backup2.read_text() == "data v2"
        
        print(f"  ✓ Multiple backups with unique timestamps")
        return True


def test_sync_algorithm():
    """Test complete sync algorithm"""
    print("\nTest 12: Complete sync algorithm...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        backup_dir = Path(tmpdir) / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create test scenario
        (local_dir / "only_local.dat").write_text("local data")
        (cloud_dir / "only_cloud.dat").write_text("cloud data")
        (local_dir / "same.dat").write_text("same data")
        (cloud_dir / "same.dat").write_text("same data")
        
        engine = SyncEngine()
        results = engine.sync_files(local_dir, cloud_dir, backup_dir)
        
        assert results["success"]
        assert results["files_synced"] >= 2  # only_local and only_cloud
        assert results["conflicts"] == 0
        
        # Verify files were synced
        assert (cloud_dir / "only_local.dat").exists()
        assert (local_dir / "only_cloud.dat").exists()
        
        print(f"  ✓ Synced {results['files_synced']} files")
        return True


def test_sync_with_backup():
    """Test sync creates backups before overwriting"""
    print("\nTest 13: Sync with backup creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        backup_dir = Path(tmpdir) / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create files that will be overwritten
        local_file = local_dir / "save.dat"
        cloud_file = cloud_dir / "save.dat"
        
        cloud_file.write_text("old cloud data")
        time.sleep(0.1)
        local_file.write_text("new local data")
        
        engine = SyncEngine()
        results = engine.sync_files(local_dir, cloud_dir, backup_dir)
        
        assert results["success"]
        
        # Check backup was created
        backups = list(backup_dir.glob("*.backup"))
        assert len(backups) >= 1
        assert any("cloud.backup" in b.name for b in backups)
        
        # Verify cloud file was updated
        assert cloud_file.read_text() == "new local data"
        
        print(f"  ✓ Created {len(backups)} backup(s) before overwriting")
        return True


def test_dry_run():
    """Test dry-run mode"""
    print("\nTest 14: Dry-run mode...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_dir = Path(tmpdir) / "local"
        cloud_dir = Path(tmpdir) / "cloud"
        backup_dir = Path(tmpdir) / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create test file
        (local_dir / "test.dat").write_text("test data")
        
        engine = SyncEngine()
        results = engine.sync_files(local_dir, cloud_dir, backup_dir, dry_run=True)
        
        assert results["success"]
        
        # Verify no actual changes were made
        assert not (cloud_dir / "test.dat").exists()
        
        # But action was recorded with details
        assert len(results["actions"]) >= 1
        action = results["actions"][0]
        assert action.get("dry_run")
        assert "direction" in action
        assert "size" in action or action["action"] == "skip"
        
        print(f"  ✓ Dry-run mode works (no actual changes)")
        print(f"    Direction: {action.get('direction')}, Size: {action.get('size', 'N/A')} bytes")
        return True


def main():
    print("=== Sync Engine Tests ===\n")
    
    tests = [
        test_file_only_local,
        test_file_only_cloud,
        test_local_newer,
        test_cloud_newer,
        test_conflict_detection,
        test_sync_summary,
        test_copy_file,
        test_copy_file_permissions,
        test_disk_space_check,
        test_create_backup,
        test_backup_with_timestamp,
        test_sync_algorithm,
        test_sync_with_backup,
        test_dry_run
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print(f"\n=== Results: {sum(results)}/{len(results)} tests passed ===")
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
