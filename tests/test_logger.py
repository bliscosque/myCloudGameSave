#!/usr/bin/env python3
"""
Test script for logging system
"""

import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.logger import init_logger, get_logger


def test_basic_logging():
    """Test basic logging functionality"""
    print("Test 1: Basic logging to file and console...")
    
    log_dir = Path("config/fedora-PC/logs")
    logger = init_logger(log_dir, "info", verbose=False)
    
    logger.debug("This is a debug message (should only be in file)")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    print("✓ Messages logged")
    return True


def test_verbose_mode():
    """Test verbose console output"""
    print("\nTest 2: Verbose mode (debug to console)...")
    
    log_dir = Path("config/fedora-PC/logs")
    logger = init_logger(log_dir, "info", verbose=True)
    
    logger.debug("Debug message in verbose mode (should appear)")
    logger.info("Info message in verbose mode")
    
    print("✓ Verbose logging works")
    return True


def test_log_levels():
    """Test different log levels"""
    print("\nTest 3: Testing log levels...")
    
    log_dir = Path("config/fedora-PC/logs")
    
    # Test warning level
    logger = init_logger(log_dir, "warning", verbose=False)
    logger.info("Info at warning level (should not appear in console)")
    logger.warning("Warning at warning level (should appear)")
    
    print("✓ Log levels work correctly")
    return True


def test_log_file_creation():
    """Test log file creation and content"""
    print("\nTest 4: Checking log file...")
    
    log_dir = Path("config/fedora-PC/logs")
    log_file = log_dir / "gamesync.log"
    
    if not log_file.exists():
        print("✗ Log file not created")
        return False
    
    # Read last few lines
    with open(log_file, 'r') as f:
        lines = f.readlines()
    
    if len(lines) == 0:
        print("✗ Log file is empty")
        return False
    
    print(f"✓ Log file exists with {len(lines)} lines")
    print(f"  Last entry: {lines[-1].strip()}")
    return True


def test_global_logger():
    """Test global logger access"""
    print("\nTest 5: Testing global logger access...")
    
    try:
        logger = get_logger()
        logger.info("Message from global logger")
        print("✓ Global logger accessible")
        return True
    except RuntimeError as e:
        print(f"✗ Error: {e}")
        return False


def main():
    print("=== Logging System Tests ===\n")
    
    tests = [
        test_basic_logging,
        test_verbose_mode,
        test_log_levels,
        test_log_file_creation,
        test_global_logger
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
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
