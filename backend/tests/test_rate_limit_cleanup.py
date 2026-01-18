"""Tests for rate limit cleanup functionality in main.py."""

import os
import time
import pytest
from unittest.mock import patch

# Set REQUIRE_AUTH=False before importing main to avoid RuntimeError
os.environ.setdefault("REQUIRE_AUTH", "False")


class TestRateLimitCleanupConstants:
    """Test that cleanup constants are defined correctly."""

    def test_cleanup_interval_exists(self):
        """Test that RATE_LIMIT_CLEANUP_INTERVAL constant exists."""
        from app.main import RATE_LIMIT_CLEANUP_INTERVAL

        assert RATE_LIMIT_CLEANUP_INTERVAL == 300  # 5 minutes
        assert isinstance(RATE_LIMIT_CLEANUP_INTERVAL, int)

    def test_max_entries_exists(self):
        """Test that RATE_LIMIT_MAX_ENTRIES constant exists."""
        from app.main import RATE_LIMIT_MAX_ENTRIES

        assert RATE_LIMIT_MAX_ENTRIES == 10000
        assert isinstance(RATE_LIMIT_MAX_ENTRIES, int)


class TestCleanupFunctionExists:
    """Test that the cleanup function exists and is callable."""

    def test_cleanup_function_exists(self):
        """Test that _cleanup_stale_rate_limit_entries function exists."""
        from app.main import _cleanup_stale_rate_limit_entries

        assert callable(_cleanup_stale_rate_limit_entries)

    def test_cleanup_called_from_check_rate_limit(self):
        """Test that cleanup is called during rate limit checks."""
        from app.main import check_rate_limit

        with patch('app.main._cleanup_stale_rate_limit_entries') as mock_cleanup:
            check_rate_limit("127.0.0.1", "/test")
            mock_cleanup.assert_called_once()


class TestStaleEntryRemoval:
    """Test that stale entries are removed correctly."""

    def test_removes_entries_with_no_recent_timestamps(self):
        """Test that entries with only expired timestamps are removed."""
        from app.main import (
            request_timestamps,
            _cleanup_stale_rate_limit_entries,
            RATE_WINDOW,
            RATE_LIMIT_CLEANUP_INTERVAL,
        )
        import app.main as main_module

        # Save original state
        original_timestamps = dict(request_timestamps)
        original_last_cleanup = main_module._last_cleanup_time

        try:
            # Clear the dict
            request_timestamps.clear()

            # Add entries with expired timestamps (older than RATE_WINDOW)
            stale_time = time.time() - RATE_WINDOW - 100
            request_timestamps[("192.168.1.1", "/api/old")] = [stale_time]
            request_timestamps[("192.168.1.2", "/api/old")] = [stale_time - 50]

            # Add an entry with valid timestamps
            fresh_time = time.time() - 10  # 10 seconds ago is still valid
            request_timestamps[("192.168.1.3", "/api/fresh")] = [fresh_time]

            # Force cleanup to run by setting _last_cleanup_time to old value
            main_module._last_cleanup_time = time.time() - RATE_LIMIT_CLEANUP_INTERVAL - 100

            # Run cleanup
            _cleanup_stale_rate_limit_entries()

            # Stale entries should be removed
            assert ("192.168.1.1", "/api/old") not in request_timestamps
            assert ("192.168.1.2", "/api/old") not in request_timestamps

            # Fresh entry should remain
            assert ("192.168.1.3", "/api/fresh") in request_timestamps

        finally:
            # Restore original state
            request_timestamps.clear()
            request_timestamps.update(original_timestamps)
            main_module._last_cleanup_time = original_last_cleanup

    def test_updates_last_cleanup_time(self):
        """Test that _last_cleanup_time is updated after cleanup runs."""
        from app.main import RATE_LIMIT_CLEANUP_INTERVAL
        import app.main as main_module

        original_last_cleanup = main_module._last_cleanup_time

        try:
            # Set last cleanup to old value to force cleanup to run
            old_time = time.time() - RATE_LIMIT_CLEANUP_INTERVAL - 100
            main_module._last_cleanup_time = old_time

            from app.main import _cleanup_stale_rate_limit_entries
            before_cleanup = time.time()
            _cleanup_stale_rate_limit_entries()
            after_cleanup = time.time()

            # Last cleanup time should be updated to current time
            assert main_module._last_cleanup_time >= before_cleanup
            assert main_module._last_cleanup_time <= after_cleanup

        finally:
            main_module._last_cleanup_time = original_last_cleanup


class TestMaxEntriesLimit:
    """Test that max entries limit is respected."""

    def test_removes_oldest_entries_when_over_limit(self):
        """Test that oldest entries are removed when exceeding RATE_LIMIT_MAX_ENTRIES."""
        from app.main import (
            request_timestamps,
            _cleanup_stale_rate_limit_entries,
            RATE_LIMIT_CLEANUP_INTERVAL,
        )
        import app.main as main_module

        # Save original state
        original_timestamps = dict(request_timestamps)
        original_last_cleanup = main_module._last_cleanup_time
        original_max_entries = main_module.RATE_LIMIT_MAX_ENTRIES

        try:
            # Clear and temporarily set a lower max for testing
            request_timestamps.clear()
            main_module.RATE_LIMIT_MAX_ENTRIES = 5

            # Add more entries than the limit, with varying timestamps
            base_time = time.time()
            for i in range(10):
                # Create entries with fresh timestamps so they aren't removed as stale
                request_timestamps[(f"ip_{i}", "/api/test")] = [base_time - i]

            # Force cleanup to run
            main_module._last_cleanup_time = base_time - RATE_LIMIT_CLEANUP_INTERVAL - 100

            # Run cleanup
            _cleanup_stale_rate_limit_entries()

            # Should be at most RATE_LIMIT_MAX_ENTRIES (5) entries
            assert len(request_timestamps) <= 5

            # The newest entries should be kept (ip_0 through ip_4 have newest timestamps)
            # Note: The cleanup keeps entries with newest max timestamp
            remaining_ips = {key[0] for key in request_timestamps.keys()}

            # Verify that we have the expected number of entries
            assert len(remaining_ips) == 5

        finally:
            # Restore original state
            request_timestamps.clear()
            request_timestamps.update(original_timestamps)
            main_module._last_cleanup_time = original_last_cleanup
            main_module.RATE_LIMIT_MAX_ENTRIES = original_max_entries


class TestCleanupInterval:
    """Test that cleanup runs periodically based on interval."""

    def test_cleanup_skipped_if_recently_run(self):
        """Test that cleanup is skipped if last cleanup was recent."""
        from app.main import RATE_LIMIT_CLEANUP_INTERVAL
        import app.main as main_module

        original_last_cleanup = main_module._last_cleanup_time

        try:
            # Set last cleanup to very recent
            recent_time = time.time() - 10  # 10 seconds ago
            main_module._last_cleanup_time = recent_time

            from app.main import _cleanup_stale_rate_limit_entries
            _cleanup_stale_rate_limit_entries()

            # Last cleanup time should not have changed (cleanup was skipped)
            assert main_module._last_cleanup_time == recent_time

        finally:
            main_module._last_cleanup_time = original_last_cleanup

    def test_cleanup_runs_after_interval(self):
        """Test that cleanup runs after interval has passed."""
        from app.main import RATE_LIMIT_CLEANUP_INTERVAL
        import app.main as main_module

        original_last_cleanup = main_module._last_cleanup_time

        try:
            # Set last cleanup to old value
            old_time = time.time() - RATE_LIMIT_CLEANUP_INTERVAL - 100
            main_module._last_cleanup_time = old_time

            from app.main import _cleanup_stale_rate_limit_entries
            _cleanup_stale_rate_limit_entries()

            # Last cleanup time should have been updated
            assert main_module._last_cleanup_time > old_time
            assert main_module._last_cleanup_time > time.time() - 10

        finally:
            main_module._last_cleanup_time = original_last_cleanup


class TestCleanupLogicIntegration:
    """Integration tests for cleanup logic with check_rate_limit."""

    def test_check_rate_limit_triggers_cleanup(self):
        """Test that check_rate_limit triggers cleanup when interval has passed."""
        from app.main import check_rate_limit, RATE_LIMIT_CLEANUP_INTERVAL
        import app.main as main_module

        original_last_cleanup = main_module._last_cleanup_time

        try:
            # Set last cleanup to old value
            old_time = time.time() - RATE_LIMIT_CLEANUP_INTERVAL - 100
            main_module._last_cleanup_time = old_time

            # Call check_rate_limit which should trigger cleanup
            check_rate_limit("127.0.0.1", "/test")

            # Last cleanup time should have been updated
            assert main_module._last_cleanup_time > old_time

        finally:
            main_module._last_cleanup_time = original_last_cleanup

    def test_expired_timestamps_removed_during_check(self):
        """Test that expired timestamps for the current key are removed during check."""
        from app.main import request_timestamps, check_rate_limit, RATE_WINDOW
        import app.main as main_module

        original_timestamps = dict(request_timestamps)
        original_last_cleanup = main_module._last_cleanup_time

        try:
            request_timestamps.clear()

            # Add expired and fresh timestamps for a specific key
            key = ("127.0.0.1", "/api/test")
            expired_time = time.time() - RATE_WINDOW - 100
            fresh_time = time.time() - 10

            request_timestamps[key] = [expired_time, fresh_time]

            # Force skip the periodic cleanup by setting recent last_cleanup_time
            main_module._last_cleanup_time = time.time()

            # Call check_rate_limit for this key
            check_rate_limit("127.0.0.1", "/api/test")

            # Expired timestamp should be removed, fresh one should remain
            # Plus the new timestamp from the check_rate_limit call
            timestamps = request_timestamps[key]
            assert all(time.time() - t < RATE_WINDOW for t in timestamps)
            assert len(timestamps) == 2  # fresh_time + new call timestamp

        finally:
            request_timestamps.clear()
            request_timestamps.update(original_timestamps)
            main_module._last_cleanup_time = original_last_cleanup
