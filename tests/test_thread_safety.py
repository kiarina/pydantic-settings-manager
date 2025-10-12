"""
Tests for thread safety of SettingsManager
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager

# Test configuration constants
DEADLOCK_TEST_TIMEOUT_SECONDS = 30  # Timeout for deadlock detection tests


class ThreadTestSettings(BaseSettings):
    """Test settings class"""

    name: str = "default"
    value: int = 0
    counter: int = 0


def test_concurrent_settings_access() -> None:
    """Test concurrent access to settings property"""
    manager = SettingsManager(ThreadTestSettings)
    manager.user_config = {"name": "test", "value": 42}

    results = []
    errors = []

    def access_settings(thread_id: int) -> None:
        try:
            for _ in range(100):
                settings = manager.settings
                results.append((thread_id, settings.name, settings.value))
                time.sleep(0.001)  # Small delay to increase chance of race conditions
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Run multiple threads concurrently
    threads = []
    for i in range(10):
        thread = threading.Thread(target=access_settings, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 1000  # 10 threads * 100 iterations

    # All results should be consistent
    for _thread_id, name, value in results:
        assert name == "test"
        assert value == 42


def test_concurrent_config_updates() -> None:
    """Test concurrent updates to user_config"""
    manager = SettingsManager(ThreadTestSettings)

    results = []
    errors = []

    def update_config(thread_id: int) -> None:
        try:
            for i in range(50):
                config = {
                    "name": f"thread_{thread_id}",
                    "value": i,
                    "counter": thread_id * 1000 + i,
                }
                manager.user_config = config

                # Immediately read back to verify
                settings = manager.settings
                results.append((thread_id, settings.name, settings.value, settings.counter))
                time.sleep(0.001)
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Run multiple threads concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=update_config, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 250  # 5 threads * 50 iterations


def test_concurrent_cli_args_updates() -> None:
    """Test concurrent updates to cli_args"""
    manager = SettingsManager(ThreadTestSettings)
    manager.user_config = {"name": "base", "value": 0}

    results = []
    errors = []

    def update_cli_args(thread_id: int) -> None:
        try:
            for i in range(50):
                manager.cli_args = {"value": thread_id * 100 + i}

                # Immediately read back to verify
                settings = manager.settings
                results.append((thread_id, settings.name, settings.value))
                time.sleep(0.001)
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Run multiple threads concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=update_cli_args, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 250  # 5 threads * 50 iterations

    # All results should have the base name
    for _thread_id, name, _value in results:
        assert name == "base"


def test_concurrent_multi_mode_operations() -> None:
    """Test concurrent operations in multi mode"""
    manager = SettingsManager(ThreadTestSettings, multi=True)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 1},
            "prod": {"name": "production", "value": 2},
            "test": {"name": "testing", "value": 3},
        }
    }

    results = []
    errors = []

    def switch_and_read(thread_id: int) -> None:
        try:
            keys = ["dev", "prod", "test"]
            for i in range(100):
                key = keys[i % len(keys)]
                manager.active_key = key

                settings = manager.settings
                results.append((thread_id, key, settings.name, settings.value))
                time.sleep(0.001)
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Run multiple threads concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=switch_and_read, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 500  # 5 threads * 100 iterations


def test_concurrent_cache_invalidation() -> None:
    """Test concurrent cache invalidation and rebuilding"""
    manager = SettingsManager(ThreadTestSettings)
    manager.user_config = {"name": "initial", "value": 0}

    results = []
    errors = []

    def invalidate_and_read(thread_id: int) -> None:
        try:
            for i in range(50):
                # Clear cache
                manager.clear()

                # Update config
                manager.user_config = {"name": f"thread_{thread_id}", "value": i}

                # Read settings (should rebuild cache)
                settings = manager.settings
                results.append((thread_id, settings.name, settings.value))
                time.sleep(0.001)
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Run multiple threads concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=invalidate_and_read, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 250  # 5 threads * 50 iterations


def test_concurrent_property_access() -> None:
    """Test concurrent access to various properties"""
    manager = SettingsManager(ThreadTestSettings, multi=True)
    manager.user_config = {
        "map": {
            "dev": {"name": "development", "value": 1},
            "prod": {"name": "production", "value": 2},
        }
    }
    manager.active_key = "dev"

    results = []
    errors = []

    def access_properties(thread_id: int) -> None:
        try:
            for _i in range(100):
                # Access various properties
                user_config = manager.user_config
                cli_args = manager.cli_args
                active_key = manager.active_key
                all_settings = manager.all_settings

                results.append(
                    (thread_id, len(user_config), len(cli_args), active_key, len(all_settings))
                )
                time.sleep(0.001)
        except Exception as e:
            errors.append((thread_id, str(e)))

    # Run multiple threads concurrently
    threads = []
    for i in range(5):
        thread = threading.Thread(target=access_properties, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Check that no errors occurred
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 500  # 5 threads * 100 iterations


def test_thread_pool_executor() -> None:
    """Test using ThreadPoolExecutor for more controlled concurrent testing"""
    manager = SettingsManager(ThreadTestSettings)
    manager.user_config = {"name": "base", "value": 0}

    def worker(worker_id: int) -> tuple[int, str, int]:
        # Update CLI args
        manager.cli_args = {"value": worker_id * 10}

        # Get settings
        settings = manager.settings
        return (worker_id, settings.name, settings.value)

    # Use ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(100)]

        results = []
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                pytest.fail(f"Worker failed with exception: {e}")

    # Check results
    assert len(results) == 100

    # All should have the base name
    for _worker_id, name, _value in results:
        assert name == "base"


def test_deadlock_prevention() -> None:
    """Test that our locking strategy doesn't cause deadlocks"""
    manager = SettingsManager(ThreadTestSettings, multi=True)
    manager.user_config = {
        "map": {
            "config1": {"name": "config1", "value": 1},
            "config2": {"name": "config2", "value": 2},
        }
    }

    def complex_operations(thread_id: int) -> None:
        """Perform complex operations that could potentially cause deadlocks"""
        for i in range(50):
            # Mix of different operations
            manager.active_key = "config1" if i % 2 == 0 else "config2"
            _ = manager.settings
            _ = manager.all_settings
            _ = manager.user_config
            manager.cli_args = {"counter": i}
            _ = manager.cli_args
            manager.clear()
            _ = manager.settings  # This should rebuild cache

    # Run multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=complex_operations, args=(i,))
        threads.append(thread)
        thread.start()

    # Set a timeout to detect potential deadlocks
    start_time = time.time()
    timeout = DEADLOCK_TEST_TIMEOUT_SECONDS

    for thread in threads:
        remaining_time = timeout - (time.time() - start_time)
        if remaining_time <= 0:
            pytest.fail("Test timed out - possible deadlock detected")

        thread.join(timeout=remaining_time)
        if thread.is_alive():
            pytest.fail("Thread did not complete - possible deadlock detected")

    # If we get here, no deadlock occurred
    assert True
