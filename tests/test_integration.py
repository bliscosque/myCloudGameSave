#!/usr/bin/env python3
"""Integration tests for end-to-end workflows"""

import sys
import os
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager
from src.game_detector import GameDetector
from src.sync_engine import SyncEngine
from src.conflict_resolver import ConflictResolver, ResolutionStrategy


def test_end_to_end_sync_workflow():
    """Test complete sync workflow from detection to sync"""
    print("\nTest 1: End-to-end sync workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Setup directories
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        backup_dir = tmpdir / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        backup_dir.mkdir()
        
        # Create test save files
        (local_dir / "save1.dat").write_text("save data 1")
        (local_dir / "save2.dat").write_text("save data 2")
        
        # Perform sync
        sync_engine = SyncEngine()
        results = sync_engine.sync_files(local_dir, cloud_dir, backup_dir)
        
        # Verify sync
        assert results["success"]
        assert results["files_synced"] == 2
        assert (cloud_dir / "save1.dat").exists()
        assert (cloud_dir / "save2.dat").exists()
        assert (cloud_dir / "save1.dat").read_text() == "save data 1"
        
        # Modify cloud file
        time.sleep(0.1)
        (cloud_dir / "save1.dat").write_text("modified in cloud")
        
        # Sync back
        results = sync_engine.sync_files(local_dir, cloud_dir, backup_dir)
        
        # Verify cloud changes synced to local
        assert results["success"]
        assert (local_dir / "save1.dat").read_text() == "modified in cloud"
        
        print("  ✓ End-to-end sync workflow works")
        return True


def test_conflict_resolution_workflow():
    """Test complete conflict detection and resolution workflow"""
    print("\nTest 2: Conflict resolution workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        backup_dir = tmpdir / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        backup_dir.mkdir()
        
        # Create initial file
        (local_dir / "save.dat").write_text("initial")
        (cloud_dir / "save.dat").write_text("initial")
        
        # Record sync time
        last_sync = datetime.now().isoformat()
        time.sleep(0.1)
        
        # Modify both (create conflict)
        (local_dir / "save.dat").write_text("local change")
        (cloud_dir / "save.dat").write_text("cloud change")
        
        # Detect conflict
        sync_engine = SyncEngine()
        comparisons = sync_engine.compare_directories(local_dir, cloud_dir, last_sync)
        
        conflicts = [c for c in comparisons if c.action.value == 'conflict']
        assert len(conflicts) == 1
        
        # Resolve conflict (keep local)
        resolver = ConflictResolver()
        conflict = conflicts[0]
        resolver.resolve_conflict(
            conflict.local_path,
            conflict.cloud_path,
            ResolutionStrategy.KEEP_LOCAL,
            backup_dir
        )
        
        # Verify resolution
        assert (cloud_dir / "save.dat").read_text() == "local change"
        
        # Verify backup was created
        backups = list(backup_dir.glob("*.conflict"))
        assert len(backups) == 2  # local and cloud backups
        
        print("  ✓ Conflict resolution workflow works")
        return True


def test_game_detection_workflow():
    """Test game detection with mock Steam data"""
    print("\nTest 3: Game detection workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create mock Steam structure
        steam_dir = tmpdir / "Steam"
        userdata_dir = steam_dir / "userdata" / "12345" / "config"
        userdata_dir.mkdir(parents=True)
        
        # Create mock shortcuts.vdf (simplified)
        shortcuts_file = userdata_dir / "shortcuts.vdf"
        # Note: Real VDF parsing requires binary format, this is just structure test
        
        # Test detector initialization
        detector = GameDetector()
        
        # Verify detector can be initialized
        assert detector is not None
        assert detector.os_type in ['linux', 'windows']
        
        print("  ✓ Game detection workflow initialized")
        return True


def test_backup_workflow():
    """Test backup creation during sync"""
    print("\nTest 4: Backup workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        backup_dir = tmpdir / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        backup_dir.mkdir()
        
        # Create initial files
        (local_dir / "save.dat").write_text("version 1")
        (cloud_dir / "save.dat").write_text("version 1")
        
        # Sync with last_sync set
        last_sync = datetime.now().isoformat()
        time.sleep(0.1)
        
        # Modify local (newer)
        (local_dir / "save.dat").write_text("version 2")
        
        # Sync (should backup cloud before overwriting)
        sync_engine = SyncEngine()
        results = sync_engine.sync_files(local_dir, cloud_dir, backup_dir, last_sync)
        
        # Verify backup was created
        backups = list(backup_dir.glob("*.backup"))
        assert len(backups) == 1
        assert "cloud" in backups[0].name
        assert backups[0].read_text() == "version 1"
        
        # Verify cloud was updated
        assert (cloud_dir / "save.dat").read_text() == "version 2"
        
        print("  ✓ Backup workflow works")
        return True


def test_dry_run_workflow():
    """Test dry-run mode doesn't make changes"""
    print("\nTest 5: Dry-run workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        backup_dir = tmpdir / "backups"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create test file
        (local_dir / "save.dat").write_text("test data")
        
        # Dry-run sync
        sync_engine = SyncEngine()
        results = sync_engine.sync_files(local_dir, cloud_dir, backup_dir, dry_run=True)
        
        # Verify no changes were made
        assert not (cloud_dir / "save.dat").exists()
        
        # But action was recorded
        assert len(results["actions"]) == 1
        assert results["actions"][0].get("dry_run")
        
        print("  ✓ Dry-run workflow works")
        return True


def test_directional_sync_to_cloud_workflow():
    """Test sync-to-cloud workflow"""
    print("\nTest 6: Directional sync-to-cloud workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create newer local file
        local_file = local_dir / "save.dat"
        local_file.write_text("new local data")
        
        # Create older cloud file
        cloud_file = cloud_dir / "save.dat"
        cloud_file.write_text("old cloud data")
        old_time = time.time() - 100
        os.utime(cloud_file, (old_time, old_time))
        
        # Sync to cloud
        sync_engine = SyncEngine()
        result = sync_engine.sync_to_cloud(local_dir, cloud_dir)
        
        # Verify cloud was updated
        assert result['total_copied'] == 1
        assert cloud_file.read_text() == "new local data"
        
        print("  ✓ Directional sync-to-cloud workflow works")
        return True


def test_directional_sync_from_cloud_workflow():
    """Test sync-from-cloud workflow"""
    print("\nTest 7: Directional sync-from-cloud workflow...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create older local file
        local_file = local_dir / "save.dat"
        local_file.write_text("old local data")
        old_time = time.time() - 100
        os.utime(local_file, (old_time, old_time))
        
        # Create newer cloud file
        cloud_file = cloud_dir / "save.dat"
        cloud_file.write_text("new cloud data")
        
        # Sync from cloud
        sync_engine = SyncEngine()
        result = sync_engine.sync_from_cloud(local_dir, cloud_dir)
        
        # Verify local was updated
        assert result['total_copied'] == 1
        assert local_file.read_text() == "new cloud data"
        
        print("  ✓ Directional sync-from-cloud workflow works")
        return True


def test_directional_sync_safety():
    """Test directional sync safety (doesn't overwrite newer files)"""
    print("\nTest 8: Directional sync safety checks...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create newer cloud file
        cloud_file = cloud_dir / "save.dat"
        cloud_file.write_text("newer cloud data")
        
        # Create older local file
        local_file = local_dir / "save.dat"
        local_file.write_text("older local data")
        old_time = time.time() - 100
        os.utime(local_file, (old_time, old_time))
        
        # Try to sync to cloud (should skip)
        sync_engine = SyncEngine()
        result = sync_engine.sync_to_cloud(local_dir, cloud_dir)
        
        # Verify cloud was NOT overwritten
        assert result['total_copied'] == 0
        assert result['total_skipped'] == 1
        assert cloud_file.read_text() == "newer cloud data"
        
        print("  ✓ Directional sync safety works (skipped newer cloud file)")
        return True


def test_directional_sync_force():
    """Test directional sync with force flag"""
    print("\nTest 9: Directional sync with --force flag...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        local_dir = tmpdir / "local"
        cloud_dir = tmpdir / "cloud"
        local_dir.mkdir()
        cloud_dir.mkdir()
        
        # Create newer cloud file
        cloud_file = cloud_dir / "save.dat"
        cloud_file.write_text("newer cloud data")
        
        # Create older local file
        local_file = local_dir / "save.dat"
        local_file.write_text("older local data")
        old_time = time.time() - 100
        os.utime(local_file, (old_time, old_time))
        
        # Force sync to cloud
        sync_engine = SyncEngine()
        result = sync_engine.sync_to_cloud(local_dir, cloud_dir, force=True)
        
        # Verify cloud WAS overwritten
        assert result['total_copied'] == 1
        assert cloud_file.read_text() == "older local data"
        
        print("  ✓ Force flag overrides safety check")
        return True


def run_all_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)
    
    tests = [
        test_end_to_end_sync_workflow,
        test_conflict_resolution_workflow,
        test_game_detection_workflow,
        test_backup_workflow,
        test_dry_run_workflow,
        test_directional_sync_to_cloud_workflow,
        test_directional_sync_from_cloud_workflow,
        test_directional_sync_safety,
        test_directional_sync_force,
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
    
    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("=" * 60)
    
    if failed == 0:
        print("✓ All integration tests passed!")
        return True
    else:
        print(f"✗ {failed} test(s) failed")
        return False


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
