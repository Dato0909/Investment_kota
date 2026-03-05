"""
JSONキャッシュ管理モジュール
Yahoo Finance APIの結果を24時間キャッシュして、API呼び出しを最小化します
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional


class Cache:
    """JSONファイルベースのキャッシュマネージャー"""

    def __init__(self, cache_dir: str = "data/cache", ttl_hours: float = 24.0):
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_hours * 3600
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, key: str) -> Path:
        safe_key = key.replace("/", "_").replace(":", "_").replace(".", "_")
        return self.cache_dir / f"{safe_key}.json"

    def get(self, key: str) -> Optional[Any]:
        """キャッシュからデータを取得。期限切れまたは存在しない場合はNoneを返す"""
        path = self._cache_path(key)
        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                entry = json.load(f)

            if time.time() - entry.get("timestamp", 0) > self.ttl_seconds:
                path.unlink(missing_ok=True)
                return None

            return entry.get("data")
        except (json.JSONDecodeError, KeyError, OSError):
            return None

    def set(self, key: str, data: Any) -> None:
        """データをキャッシュに保存"""
        path = self._cache_path(key)
        entry = {
            "timestamp": time.time(),
            "data": data,
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

    def delete(self, key: str) -> None:
        """キャッシュエントリを削除"""
        self._cache_path(key).unlink(missing_ok=True)

    def clear_expired(self) -> int:
        """期限切れキャッシュを一括削除。削除件数を返す"""
        count = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if time.time() - entry.get("timestamp", 0) > self.ttl_seconds:
                    path.unlink()
                    count += 1
            except (json.JSONDecodeError, KeyError, OSError):
                path.unlink(missing_ok=True)
                count += 1
        return count

    def clear_all(self) -> int:
        """全キャッシュを削除"""
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink(missing_ok=True)
            count += 1
        return count

    def info(self) -> dict:
        """キャッシュ統計情報を返す"""
        total = 0
        valid = 0
        expired = 0
        size_bytes = 0

        for path in self.cache_dir.glob("*.json"):
            total += 1
            size_bytes += path.stat().st_size
            try:
                with open(path, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                if time.time() - entry.get("timestamp", 0) <= self.ttl_seconds:
                    valid += 1
                else:
                    expired += 1
            except (json.JSONDecodeError, KeyError, OSError):
                expired += 1

        return {
            "total_entries": total,
            "valid_entries": valid,
            "expired_entries": expired,
            "total_size_kb": round(size_bytes / 1024, 1),
            "ttl_hours": self.ttl_seconds / 3600,
        }
