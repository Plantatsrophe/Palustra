"""Local field caching engine for zero-connectivity botanical operations."""

import hashlib
import json
import time
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import RLock

from app.config import settings

class LocalFieldCache:
    """Thread-safe In-Memory LRU Cache with TTL and disk snapshot support for field operations."""

    def __init__(
        self,
        max_size: int = settings.cache_max_size,
        ttl_seconds: int = settings.cache_ttl_seconds,
        cache_dir: Optional[Path] = None,
    ):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache: OrderedDict[str, Tuple[float, Any]] = OrderedDict()
        self._lock = RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _generate_key(self, prefix: str, **kwargs: Any) -> str:
        """Generate deterministic cache key."""
        sorted_items = sorted(kwargs.items())
        serialized = json.dumps(sorted_items, sort_keys=True)
        h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"{prefix}:{h}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve item from cache if present and not expired."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            timestamp, value = self._cache[key]
            if time.time() - timestamp > self.ttl:
                # Expired
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            # Move to end for LRU order
            self._cache.move_to_end(key)
            self._stats["hits"] += 1
            return value

    def set(self, key: str, value: Any) -> None:
        """Store item in cache with current timestamp, evicting oldest if capacity reached."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                self._stats["evictions"] += 1

            self._cache[key] = (time.time(), value)

    def invalidate(self, prefix: Optional[str] = None) -> int:
        """Invalidate entries matching prefix or clear all if prefix is None."""
        with self._lock:
            if prefix is None:
                count = len(self._cache)
                self._cache.clear()
                return count

            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """Return cache hit/miss/size telemetry."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_ratio = (
                (self._stats["hits"] / total_requests) if total_requests > 0 else 0.0
            )
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "hit_ratio": round(hit_ratio, 4),
            }

    def save_offline_snapshot(self, filename: str, data: Dict[str, Any]) -> Path:
        """Save a structured JSON snapshot for offline PWA field client caching."""
        target_path = self.cache_dir / filename
        with self._lock:
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        return target_path

    def load_offline_snapshot(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load an offline field snapshot if available."""
        target_path = self.cache_dir / filename
        if not target_path.exists():
            return None
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

# Global singleton cache instance
field_cache = LocalFieldCache()
