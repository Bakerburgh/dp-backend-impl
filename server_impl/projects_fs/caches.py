from typing import Callable, List, TypeVar, Generic
from glob import glob
import os


class GlobCache:
    def __init__(self, pattern: str, accessor: Callable, accessor_args: List = None):
        self.pattern = pattern
        self.accessor = accessor
        if accessor_args:
            self.args = accessor_args
        else:
            self.args = []
        self._data = None
        self.cached_time = self.last_modified()

    def last_modified(self) -> float:
        files = glob(self.pattern)
        if len(files) == 0:
            return 0
        return max([os.path.getmtime(x) for x in files])

    @property
    def data(self):
        m = self.last_modified()
        if self._data is not None:
            if m == self.cached_time:
                # No changes, return cached version
                print('CACHE HIT')
                return self._data
        self.cached_time = m
        print('CACHE MISS')
        self._data = self.accessor(*self.args)
        return self._data

    def filter(self, filter_fn):
        # Cache may be empty, in which case there is nothing to do...
        if self._data:
            self._data = filter(filter_fn, self._data)


class CacheMap:

    def __init__(self, pattern: Callable, accessor: Callable):
        """
        Build a map from some key to a glob cache per key.
        :param pattern: A function that returns the glob pattern for this key.
        :type pattern: (str) -> str
        :param accessor: A function that takes the key returns the data for use in the cache.
        :type accessor: (str) -> obj
        """
        self.patternBuilder = pattern
        self.caches = dict()
        self.accessor = accessor

    def of(self, key):
        cache = self.caches.get(key)
        if cache is None:
            cache = GlobCache(self.patternBuilder(key), self.accessor, [key])
            self.caches[key] = cache
        return cache

    def remove(self, key):
        if key in self.caches:
            del self.caches[key]


T = TypeVar('T')


class CacheDoubleMap(Generic[T]):

    def __init__(self, pattern: Callable[[str, str], str], accessor: Callable[[str, str], T]):
        """
        Build a map from some key to a glob cache per key.
        :param pattern: A function that returns the glob pattern for these two keys.
        :type pattern: (str, str) -> str
        :param accessor: A function that takes the key returns the data for use in the cache.
        :type accessor: (str, str) -> obj
        """
        self.patternBuilder = pattern
        self.caches = dict()
        self.accessor = accessor

    def _compound_key(self, key1: str, key2: str) -> str:
        return "%s ~.~ %s" % (key1, key2)

    def of(self, key1: str, key2: str):
        ckey = self._compound_key(key1, key2)
        cache = self.caches.get(ckey)
        if cache is None:
            cache = GlobCache(self.patternBuilder(key1, key2), self.accessor, [key1, key2])
            self.caches[ckey] = cache
        return cache

    def remove(self, key1: str, key2: str):
        ckey = self._compound_key(key1, key2)
        if ckey in self.caches:
            del self.caches[ckey]