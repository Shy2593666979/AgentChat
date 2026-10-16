from threading import RLock
from time import monotonic

from cachetools import LRUCache


class MemoryCacheConnection:
    """单进程缓存，兼容项目使用的 Redis 操作并保留过期语义。"""

    def __init__(self):
        self._values = LRUCache(maxsize=10000)
        self._lock = RLock()

    def _get(self, key):
        item = self._values.get(key)
        if item is None:
            return None
        value, expires = item
        if expires is not None and monotonic() >= expires:
            self._values.pop(key, None)
            return None
        return value

    def get(self, key):
        with self._lock:
            return self._get(key)

    def setnx(self, key, value):
        with self._lock:
            if self._get(key) is not None:
                return False
            self._values[key] = (value, None)
            return True

    def setex(self, key, expiration, value):
        with self._lock:
            self._values[key] = (value, monotonic() + expiration)
            return True

    def expire(self, key, expiration):
        with self._lock:
            value = self._get(key)
            if value is None:
                return False
            self._values[key] = (value, monotonic() + expiration)
            return True

    def hset(self, name, key=None, value=None, mapping=None, items=None):
        with self._lock:
            values = dict(self._get(name) or {})
            updates = dict(mapping or {})
            if key is not None:
                updates[key] = value
            if items:
                updates.update(zip(items[::2], items[1::2]))
            added = len(updates.keys() - values.keys())
            values.update(updates)
            expires = self._values[name][1] if name in self._values else None
            self._values[name] = (values, expires)
            return added

    def hget(self, name, key):
        with self._lock:
            return (self._get(name) or {}).get(key)

    def hgetall(self, name):
        with self._lock:
            return dict(self._get(name) or {})

    def delete(self, key):
        with self._lock:
            exists = self._get(key) is not None
            self._values.pop(key, None)
            return int(exists)

    def incr(self, key):
        with self._lock:
            value = int(self._get(key) or 0) + 1
            expires = self._values[key][1] if key in self._values else None
            self._values[key] = (value, expires)
            return value

    def close(self):
        # 与 Redis 连接关闭保持接口兼容，不清空进程内的缓存数据。
        pass
