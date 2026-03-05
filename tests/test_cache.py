"""
キャッシュモジュールのテスト
"""

import json
import time
import tempfile
from pathlib import Path

import pytest

from src.data.cache import Cache


@pytest.fixture
def tmp_cache(tmp_path):
    """一時ディレクトリを使用したキャッシュのフィクスチャ"""
    return Cache(cache_dir=str(tmp_path / "cache"), ttl_hours=1.0)


class TestCache:
    def test_set_and_get(self, tmp_cache):
        tmp_cache.set("key1", {"value": 42})
        result = tmp_cache.get("key1")
        assert result == {"value": 42}

    def test_get_nonexistent(self, tmp_cache):
        result = tmp_cache.get("nonexistent")
        assert result is None

    def test_get_expired(self, tmp_cache):
        cache = Cache(cache_dir=tmp_cache.cache_dir, ttl_hours=0.0001)  # 0.36秒
        cache.set("key_exp", "data")
        time.sleep(0.5)
        result = cache.get("key_exp")
        assert result is None

    def test_delete(self, tmp_cache):
        tmp_cache.set("key2", "value2")
        tmp_cache.delete("key2")
        assert tmp_cache.get("key2") is None

    def test_clear_all(self, tmp_cache):
        tmp_cache.set("a", 1)
        tmp_cache.set("b", 2)
        tmp_cache.set("c", 3)
        count = tmp_cache.clear_all()
        assert count == 3
        assert tmp_cache.get("a") is None

    def test_clear_expired(self, tmp_cache):
        # 有効なキャッシュと期限切れを混在
        tmp_cache.set("valid", "ok")
        cache_dir = Path(tmp_cache.cache_dir)
        expired_path = cache_dir / "expired_key.json"
        with open(expired_path, "w") as f:
            json.dump({"timestamp": 0, "data": "old"}, f)

        count = tmp_cache.clear_expired()
        assert count >= 1
        assert tmp_cache.get("valid") == "ok"

    def test_info(self, tmp_cache):
        tmp_cache.set("x", 1)
        tmp_cache.set("y", 2)
        info = tmp_cache.info()
        assert info["total_entries"] == 2
        assert info["valid_entries"] == 2
        assert info["expired_entries"] == 0

    def test_special_chars_in_key(self, tmp_cache):
        tmp_cache.set("ticker/AAPL:info.json", {"price": 150})
        result = tmp_cache.get("ticker/AAPL:info.json")
        assert result == {"price": 150}

    def test_various_data_types(self, tmp_cache):
        tmp_cache.set("list", [1, 2, 3])
        tmp_cache.set("string", "hello")
        tmp_cache.set("number", 3.14)
        tmp_cache.set("none", None)

        assert tmp_cache.get("list") == [1, 2, 3]
        assert tmp_cache.get("string") == "hello"
        assert tmp_cache.get("number") == 3.14
        assert tmp_cache.get("none") is None
