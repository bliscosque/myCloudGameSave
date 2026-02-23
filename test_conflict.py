#!/usr/bin/env python3
"""Tests for conflict resolution"""

import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from src.conflict_resolver import ConflictResolver, ResolutionStrategy


def test_conflict_detection():
    """Test conflict detection"""
    print("\nTest 1: Conflict detection...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        # Create files with different timestamps (ensure > 2 second difference)
        local_path.write_text("local version")
        time.sleep(2.5)
        cloud_path.write_text("cloud version")
        
        resolver = ConflictResolver()
        
        # Should detect conflict (no last_sync)
        assert resolver.detect_conflict(local_path, cloud_path)
        
        print("  ✓ Conflict detected when files differ")
        return True


def test_no_conflict_same_time():
    """Test no conflict when files have same timestamp"""
    print("\nTest 2: No conflict with same timestamp...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        # Create identical files
        local_path.write_text("same content")
        cloud_path.write_text("same content")
        
        resolver = ConflictResolver()
        
        # Should not detect conflict
        assert not resolver.detect_conflict(local_path, cloud_path)
        
        print("  ✓ No conflict when timestamps are same")
        return True


def test_conflict_with_last_sync():
    """Test conflict detection with last_sync timestamp"""
    print("\nTest 3: Conflict detection with last_sync...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        # Set last sync to 1 hour ago
        last_sync = (datetime.now() - timedelta(hours=1)).isoformat()
        
        # Create files (both newer than last_sync)
        local_path.write_text("local version")
        cloud_path.write_text("cloud version")
        
        resolver = ConflictResolver()
        
        # Should detect conflict (both modified after last_sync)
        assert resolver.detect_conflict(local_path, cloud_path, last_sync)
        
        print("  ✓ Conflict detected when both files newer than last_sync")
        return True


def test_conflict_backup():
    """Test conflict backup creation"""
    print("\nTest 4: Conflict backup creation...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        backup_dir = Path(tmpdir) / "backups"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        local_path.write_text("local content")
        cloud_path.write_text("cloud content")
        
        resolver = ConflictResolver()
        backups = resolver.create_conflict_backup(local_path, cloud_path, backup_dir)
        
        assert "local" in backups
        assert "cloud" in backups
        assert backups["local"].exists()
        assert backups["cloud"].exists()
        assert "conflict" in backups["local"].name
        assert "conflict" in backups["cloud"].name
        
        print(f"  ✓ Created backups: {backups['local'].name}, {backups['cloud'].name}")
        return True


def test_conflict_info():
    """Test getting conflict information"""
    print("\nTest 5: Get conflict information...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        local_path.write_text("local")
        cloud_path.write_text("cloud data")
        
        resolver = ConflictResolver()
        info = resolver.get_conflict_info(local_path, cloud_path)
        
        assert info["filename"] == "save.dat"
        assert info["local"]["size"] == 5
        assert info["cloud"]["size"] == 10
        assert "modified" in info["local"]
        assert "modified" in info["cloud"]
        
        print(f"  ✓ Got conflict info: local={info['local']['size']}B, cloud={info['cloud']['size']}B")
        return True


def test_resolve_keep_local():
    """Test resolving conflict by keeping local"""
    print("\nTest 6: Resolve conflict - keep local...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        backup_dir = Path(tmpdir) / "backups"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        local_path.write_text("local version")
        cloud_path.write_text("cloud version")
        
        resolver = ConflictResolver()
        success = resolver.resolve_conflict(
            local_path, cloud_path, 
            ResolutionStrategy.KEEP_LOCAL, 
            backup_dir
        )
        
        assert success
        assert cloud_path.read_text() == "local version"
        
        print("  ✓ Kept local version, copied to cloud")
        return True


def test_resolve_keep_cloud():
    """Test resolving conflict by keeping cloud"""
    print("\nTest 7: Resolve conflict - keep cloud...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        backup_dir = Path(tmpdir) / "backups"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        local_path.write_text("local version")
        cloud_path.write_text("cloud version")
        
        resolver = ConflictResolver()
        success = resolver.resolve_conflict(
            local_path, cloud_path, 
            ResolutionStrategy.KEEP_CLOUD, 
            backup_dir
        )
        
        assert success
        assert local_path.read_text() == "cloud version"
        
        print("  ✓ Kept cloud version, copied to local")
        return True


def test_resolve_keep_both():
    """Test resolving conflict by keeping both"""
    print("\nTest 8: Resolve conflict - keep both...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save.dat"
        backup_dir = Path(tmpdir) / "backups"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        local_path.write_text("local version")
        cloud_path.write_text("cloud version")
        
        resolver = ConflictResolver()
        success = resolver.resolve_conflict(
            local_path, cloud_path, 
            ResolutionStrategy.KEEP_BOTH, 
            backup_dir
        )
        
        assert success
        
        # Original files should be renamed
        local_files = list(local_path.parent.glob("save*.dat"))
        cloud_files = list(cloud_path.parent.glob("save*.dat"))
        
        assert len(local_files) == 1
        assert len(cloud_files) == 1
        assert "local" in local_files[0].name
        assert "cloud" in cloud_files[0].name
        
        print(f"  ✓ Kept both versions: {local_files[0].name}, {cloud_files[0].name}")
        return True


def test_conflict_tracking():
    """Test conflict tracking"""
    print("\nTest 9: Conflict tracking...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = Path(tmpdir) / "local" / "save1.dat"
        cloud_path = Path(tmpdir) / "cloud" / "save1.dat"
        local_path.parent.mkdir()
        cloud_path.parent.mkdir()
        
        local_path.write_text("data")
        cloud_path.write_text("data")
        
        resolver = ConflictResolver()
        
        # Add conflicts
        resolver.add_conflict(local_path, cloud_path)
        
        conflicts = resolver.list_conflicts()
        assert len(conflicts) == 1
        assert conflicts[0]["filename"] == "save1.dat"
        
        # Clear conflicts
        resolver.clear_conflicts()
        assert len(resolver.list_conflicts()) == 0
        
        print("  ✓ Conflict tracking works")
        return True


def run_all_tests():
    """Run all conflict resolver tests"""
    print("=" * 50)
    print("Running Conflict Resolver Tests")
    print("=" * 50)
    
    tests = [
        test_conflict_detection,
        test_no_conflict_same_time,
        test_conflict_with_last_sync,
        test_conflict_backup,
        test_conflict_info,
        test_resolve_keep_local,
        test_resolve_keep_cloud,
        test_resolve_keep_both,
        test_conflict_tracking,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            print(f"  ✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ Test error: {e}")
            failed += 1
    
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("=" * 50)
    
    if failed == 0:
        print("✓ All tests passed!")
        return True
    else:
        print(f"✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
