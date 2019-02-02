from guillotina import app_settings
from guillotina import configure
from guillotina.component import get_utility
from guillotina_ratelimit.interfaces import IRateLimitingStateManager

from .utils import Timer
import logging
import functools

logger = logging.getLogger('guillotina_ratelimit.state')

try:
    import aioredis
    from guillotina_rediscache.cache import get_redis_pool
except ImportError:
    aioredis = None

_EMPTY = object()


@configure.utility(provides=IRateLimitingStateManager, name='memory')
class MemoryRateLimitingStateManager:
    """For testing purposes only
    """
    def __init__(self):
        self._counts = {}
        self._timers = {}

    def set_loop(self, loop=None):
        pass

    async def increment(self, user, key):
        self._counts.setdefault(user, {})
        self._counts[user].setdefault(key, 0)
        self._counts[user][key] += 1

    async def get_count(self, user, key):
        return self._counts.get(user, {}).get(key, 0)

    async def _expire_key(self, user, key):
        if user in self._counts:
            self._counts[user].pop(key, None)

        if user in self._timers:
            self._timers[user].pop(key, None)

    async def expire_after(self, user, key, ttl):
        callback = functools.partial(self._expire_key, user, key)
        self._timers.setdefault(user, {})
        self._timers[user][key] = Timer(ttl, callback)

    async def get_remaining_time(self, user, key):
        if key not in self._timers.get(user, {}):
            return 0.0
        return self._timers[user][key].remaining

    async def _clean(self):
        self._counts = {}
        # Cancel current timers
        for u, _timers in self._timers.items():
            for k, timer in _timers.items():
                try:
                    timer.cancel()
                except:  # noqa
                    pass
        self._timers = {}

    async def dump_user_counts(self, user):
        counts = {}
        for key, key_count in self._counts.get(user, {}).items():
            timer = self._timers.get(user, {}).get(key)
            remaining = timer.remaining if timer else None
            if remaining:
                counts[key] = {
                    'count': key_count,
                    'remaining': remaining,
                }
        return counts


@configure.utility(provides=IRateLimitingStateManager, name='redis')
class RedisRateLimitingStateManager:
    def __init__(self):
        self.loop = None
        ratelimit_settings = app_settings.get('ratelimit', {})
        self._cache_prefix = ratelimit_settings.get('redis_prefix_key', 'ratelimit-')
        self._cache = _EMPTY

    def set_loop(self, loop=None):
        if loop:
            self.loop = loop

    async def get_cache(self):
        if self._cache != _EMPTY:
            return self._cache

        if aioredis is None:
            logger.warning('guillotina_rediscache not installed')
            self._cache = _EMPTY
            return None

        if 'redis' in app_settings:
            self._cache = aioredis.Redis(await get_redis_pool(loop=self.loop))
            return self._cache

        else:
            self._cache = _EMPTY
            raise Exception('Cache not found')

    def _build(self, some_string):
        return f'{self._cache_prefix}{some_string}'

    async def increment(self, user, key):
        cache = await self.get_cache()
        hashfield = self._build(user + key)
        await cache.hincrby(hashfield, 'count', increment=1)

    async def get_count(self, user, key):
        cache = await self.get_cache()
        hashfield = self._build(user + key)
        count = await cache.hget(hashfield, 'count')
        return int(count or b'0')

    async def expire_after(self, user, key, ttl):
        cache = await self.get_cache()
        hashfield = self._build(user + key)
        await cache.expire(hashfield, timeout=ttl)

    async def get_remaining_time(self, user, key):
        cache = await self.get_cache()
        hashfield = self._build(user + key)
        ms = await cache.pttl(hashfield)
        if not ms or ms < 0:
            return 0.0
        return ms/1000.0

    async def _clean(self):
        await self._cache.flushall()

    async def dump_user_counts(self, user):
        # TODO: improve so that we don't do so many calls to redis...
        report = {}
        async for key in self._list(user):
            key = key.lstrip(user)
            count = await self.get_count(user, key)
            remaining = await self.get_remaining_time(user, key)
            report[key] = {'count': count, 'remaining': remaining}
        return report

    async def _list(self, user):
        cache = await self.get_cache()
        async for key in cache.iscan(match=self._build(user + '*')):
            yield key.decode().replace(self._cache_prefix, '')


def get_state_manager(loop=None):
    """Returns memory persistent_manager by default
    """
    utility = get_utility(
        IRateLimitingStateManager,
        name=app_settings.get('ratelimit', {}).get('state_manager', 'redis'),
    )
    if loop:
        # This is only for testing purposes, as we need it to have the
        # same pytest loop
        utility.set_loop(loop)
    return utility
