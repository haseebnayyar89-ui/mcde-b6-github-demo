"""Task 08 | Cache Decorator with Expiration

Unhashable arguments (like a list) cannot be used as a cache key, so for such
calls the cache is skipped: the function just runs normally and counts as a miss.
"""
import functools
import time


def ttl_cache(seconds):
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)) or seconds <= 0:
        raise ValueError("seconds must be a number greater than zero")

    def decorator(func):
        cache = {}                              # key -> (result, expiry time)
        stats = {"hits": 0, "misses": 0}

        @functools.wraps(func)                  # keeps name and docstring of func
        def wrapper(*args, **kwargs):
            # sorted kwargs: x=2,y=3 and y=3,x=2 give the same key
            key = (args, tuple(sorted(kwargs.items())))
            try:
                hash(key)
            except TypeError:                   # unhashable input -> no caching
                stats["misses"] += 1
                return func(*args, **kwargs)

            if key in cache:
                result, expires_at = cache[key]
                if time.monotonic() < expires_at:
                    stats["hits"] += 1
                    return result

            stats["misses"] += 1
            result = func(*args, **kwargs)
            cache[key] = (result, time.monotonic() + seconds)
            return result

        wrapper.cache_info = lambda: dict(stats)
        return wrapper

    return decorator


if __name__ == "__main__":
    @ttl_cache(seconds=0.5)
    def add(x, y):
        """Add two numbers."""
        print("  computing...")
        return x + y

    print(add.__name__, "|", add.__doc__)
    add(x=2, y=3)
    add(y=3, x=2)                   # hit
    print(add.cache_info())         # hits 1, misses 1
    time.sleep(0.6)
    add(x=2, y=3)                   # expired -> computed again
    print(add.cache_info())         # hits 1, misses 2
