#!/usr/bin/env python3
"""Run all tests for the game sync tool"""

import sys
import subprocess
from pathlib import Path

def run_test_file(test_file):
    """Run a single test file and return results"""
    print(f"\n{'='*60}")
    print(f"Running {test_file}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        [sys.executable, test_file],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    return result.returncode == 0

def main():
    """Run all test files"""
    test_files = [
        'test_config.py',
        'test_logger.py',
        'test_detector.py',
        'test_sync.py',
        'test_conflict.py',
    ]
    
    print("="*60)
    print("Running All Tests")
    print("="*60)
    
    results = {}
    for test_file in test_files:
        if Path(test_file).exists():
            results[test_file] = run_test_file(test_file)
        else:
            print(f"⚠ Warning: {test_file} not found")
            results[test_file] = False
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_file, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_file}")
    
    print(f"\n{passed}/{total} test suites passed")
    
    if passed == total:
        print("\n✓ All test suites passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test suite(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
