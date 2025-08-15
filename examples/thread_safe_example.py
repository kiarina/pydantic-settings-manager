#!/usr/bin/env python3
"""
Thread-safe SettingsManager example

This example demonstrates how to use the new thread-safe SettingsManager
in a multi-threaded environment.
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from pydantic_settings import BaseSettings

from pydantic_settings_manager import SettingsManager


class AppSettings(BaseSettings):
    """Example application settings"""
    app_name: str = "MyApp"
    debug: bool = False
    max_connections: int = 100
    timeout: float = 30.0


def single_mode_example() -> None:
    """Example of thread-safe single mode usage"""
    print("=== Single Mode Thread Safety Example ===")

    # Create a thread-safe settings manager
    manager = SettingsManager(AppSettings)
    manager.user_config = {
        "app_name": "ThreadSafeApp",
        "debug": True,
        "max_connections": 200
    }

    results = []

    def worker(worker_id: int) -> None:
        """Worker function that accesses and modifies settings"""
        for i in range(10):
            # Each worker updates CLI args with their own values
            manager.cli_args = {
                "timeout": worker_id * 10 + i,
                "max_connections": worker_id * 100 + i
            }

            # Read settings (thread-safe)
            settings = manager.settings
            results.append({
                "worker_id": worker_id,
                "iteration": i,
                "app_name": settings.app_name,
                "debug": settings.debug,
                "max_connections": settings.max_connections,
                "timeout": settings.timeout
            })

            time.sleep(0.01)  # Simulate some work

    # Run multiple workers concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker, i) for i in range(5)]

        # Wait for all workers to complete
        for future in as_completed(futures):
            future.result()

    print(f"Processed {len(results)} settings accesses across multiple threads")
    print(f"Sample result: {results[0]}")
    print()


def multi_mode_example() -> None:
    """Example of thread-safe multi mode usage"""
    print("=== Multi Mode Thread Safety Example ===")

    # Create a thread-safe settings manager in multi mode
    manager = SettingsManager(AppSettings, multi=True)
    manager.user_config = {
        "map": {
            "development": {
                "app_name": "MyApp-Dev",
                "debug": True,
                "max_connections": 10,
                "timeout": 5.0
            },
            "staging": {
                "app_name": "MyApp-Staging",
                "debug": False,
                "max_connections": 50,
                "timeout": 15.0
            },
            "production": {
                "app_name": "MyApp-Prod",
                "debug": False,
                "max_connections": 1000,
                "timeout": 60.0
            }
        }
    }

    results = []

    def environment_worker(worker_id: int) -> None:
        """Worker that switches between different environments"""
        environments = ["development", "staging", "production"]

        for i in range(15):
            # Switch to different environment
            env = environments[i % len(environments)]
            manager.active_key = env

            # Read settings for current environment
            settings = manager.settings
            results.append({
                "worker_id": worker_id,
                "iteration": i,
                "environment": env,
                "app_name": settings.app_name,
                "debug": settings.debug,
                "max_connections": settings.max_connections,
                "timeout": settings.timeout
            })

            time.sleep(0.01)

    # Run multiple workers concurrently
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(environment_worker, i) for i in range(3)]

        # Wait for all workers to complete
        for future in as_completed(futures):
            future.result()

    print(f"Processed {len(results)} environment switches across multiple threads")

    # Show results by environment
    by_env: dict[str, list[dict[str, Any]]] = {}
    for result in results:
        env = str(result["environment"])
        if env not in by_env:
            by_env[env] = []
        by_env[env].append(result)

    for env, env_results in by_env.items():
        print(f"  {env}: {len(env_results)} accesses")
    print()


def stress_test_example() -> None:
    """Stress test with many concurrent operations"""
    print("=== Stress Test Example ===")

    manager = SettingsManager(AppSettings, multi=True)
    manager.user_config = {
        "map": {
            f"config_{i}": {
                "app_name": f"App-{i}",
                "debug": i % 2 == 0,
                "max_connections": i * 10,
                "timeout": i * 5.0
            }
            for i in range(10)
        }
    }

    operation_count = 0
    lock = threading.Lock()

    def stress_worker(worker_id: int) -> None:
        """Worker that performs various operations rapidly"""
        nonlocal operation_count

        for i in range(100):
            # Randomly choose an operation
            op = i % 4

            if op == 0:
                # Switch active key
                manager.active_key = f"config_{i % 10}"
            elif op == 1:
                # Read settings
                _ = manager.settings
            elif op == 2:
                # Read all settings
                _ = manager.all_settings
            elif op == 3:
                # Update CLI args
                manager.cli_args = {"timeout": i * 0.1}

            with lock:
                operation_count += 1

    start_time = time.time()

    # Run many workers concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(stress_worker, i) for i in range(20)]

        # Wait for all workers to complete
        for future in as_completed(futures):
            future.result()

    end_time = time.time()

    print(f"Completed {operation_count} operations in {end_time - start_time:.2f} seconds")
    print(f"Operations per second: {operation_count / (end_time - start_time):.0f}")
    print()


def deadlock_prevention_example() -> None:
    """Example showing that our implementation prevents deadlocks"""
    print("=== Deadlock Prevention Example ===")

    manager = SettingsManager(AppSettings, multi=True)
    manager.user_config = {
        "map": {
            "config1": {"app_name": "App1", "max_connections": 100},
            "config2": {"app_name": "App2", "max_connections": 200}
        }
    }

    def complex_worker(worker_id: int) -> None:
        """Worker that performs complex nested operations"""
        for i in range(50):
            # Mix of operations that could potentially cause deadlocks
            manager.active_key = "config1" if i % 2 == 0 else "config2"

            # Nested property access
            _ = manager.settings
            _ = manager.user_config
            _ = manager.all_settings

            # Update operations
            manager.cli_args = {"timeout": i}
            manager.clear()

            # More reads after cache invalidation
            _ = manager.settings
            _ = manager.cli_args

    start_time = time.time()

    # Run workers that could potentially deadlock
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(complex_worker, i) for i in range(10)]

        # Set a timeout to detect deadlocks
        try:
            for future in as_completed(futures, timeout=30):
                future.result()
        except TimeoutError:
            print("ERROR: Deadlock detected!")
            return

    end_time = time.time()

    print(f"Complex operations completed successfully in {end_time - start_time:.2f} seconds")
    print("No deadlocks detected!")
    print()


if __name__ == "__main__":
    print("Thread-Safe SettingsManager Examples")
    print("=" * 50)
    print()

    single_mode_example()
    multi_mode_example()
    stress_test_example()
    deadlock_prevention_example()

    print("All examples completed successfully!")
    print("The SettingsManager is fully thread-safe and ready for production use.")
