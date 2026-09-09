"""Unit tests for local field caching and offline snapshot storage."""

import time
import pytest

def test_cache_set_and_get(test_cache):
    test_cache.set("key1", {"data": "test"})
    val = test_cache.get("key1")
    assert val == {"data": "test"}

def test_cache_miss_and_stats(test_cache):
    val = test_cache.get("nonexistent")
    assert val is None
    stats = test_cache.get_stats()
    assert stats["misses"] >= 1

def test_cache_ttl_expiration(test_cache):
    test_cache.set("short_key", "temporary_val")
    assert test_cache.get("short_key") == "temporary_val"
    time.sleep(2.1)  # TTL is 2s in test_cache fixture
    assert test_cache.get("short_key") is None

def test_cache_lru_eviction(test_cache):
    # Capacity is 10
    for i in range(15):
        test_cache.set(f"k{i}", f"v{i}")
    stats = test_cache.get_stats()
    assert stats["size"] == 10
    assert stats["evictions"] == 5
    # Earliest keys should have been evicted
    assert test_cache.get("k0") is None
    assert test_cache.get("k14") == "v14"

def test_cache_offline_snapshot(test_cache):
    snapshot_data = {"version": "1.0", "species": ["Acer rubrum", "Carex lurida"]}
    path = test_cache.save_offline_snapshot("test_snapshot.json", snapshot_data)
    assert path.exists()

    loaded = test_cache.load_offline_snapshot("test_snapshot.json")
    assert loaded == snapshot_data
