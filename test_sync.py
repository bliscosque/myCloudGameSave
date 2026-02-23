#!/usr/bin/env python3
"""
Test script for sync engine
"""

import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

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


def main():
    print("=== Sync Engine Tests ===\n")
    
    tests = [
        test_file_only_local,
        test_file_only_cloud,
        test_local_newer,
        test_cloud_newer,
        test_conflict_detection,
        test_sync_summary
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
