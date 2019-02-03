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
        self._cache_prefix = ratelimit_settings.get('redis_prefix_key', 'ratelimit')
        self._cache = _EMPTY

    def set_loop(self, loop=None):
        if loop:
            self.loop = loop

    async def get_cache(self):
        if self._cache != _EMPTY:
            return self._cache

        if aioredis is None:
            raise Exception('guillotina_rediscache not installed')

        if 'redis' in app_settings:
            self._cache = aioredis.Redis(await get_redis_pool(loop=self.loop))
            return self._cache

        raise Exception('Cache not found')

    def _build(self, some_string):
        return f'{self._cache_prefix}-{some_string}'

    async def increment(self, user, key, timestamp):
        cache = await self.get_cache()
        request_key = self._build(';'.join([user, key, str(timestamp)]))
        await cache.hincrby(request_key, 'count', increment=1)

        # We need to add the main key aswell, where the remaining time
        # will be obtained from
        main_key = self._build(';'.join([user, key]))
        await cache.hincrby(main_key, 'count', increment=1)

    async def get_count(self, user, key):
        cache = await self.get_cache()
        request_key = self._build(';'.join([user, key]))
        request_count = 0
        async for key in cache.iscan(match=request_key + '*'):
            request_count += 1
        # There is always an extra key
        return request_count - 1 if request_count else 0

    async def expire_after(self, user, key, timestamp, ttl):
        cache = await self.get_cache()
        # We need to expire the individual keys so that redis gets
        # cleaned up eventually
        request_key = self._build(';'.join([user, key, str(timestamp)]))
        await cache.expire(request_key, timeout=ttl)

        # We use a key without the timestamp for which we always the
        # latest expiration to be able to get the remaining time
        main_key = self._build(';'.join([user, key]))
        await cache.expire(main_key, timeout=ttl)

    async def get_remaining_time(self, user, key):
        cache = await self.get_cache()
        main_key = self._build(';'.join([user, key]))
        ms = await cache.pttl(main_key)
        if not ms or ms < 0:
            return 0.0
        return ms/1000.0

    async def _clean(self):
        await self._cache.flushall()

    async def dump_user_counts(self, user):
        report = {}
        user_keys = await self._list_user_keys(user)
        for request_key in user_keys:
            count = await self.get_count(user, request_key)
            report[request_key] = {'count': count}
        return report

    async def _list_user_keys(self, user):
        cache = await self.get_cache()
        user_keys = set({})
        async for key in cache.iscan(match=self._build(user) + '*'):
            request_key = ';'.join(key.decode().split(';')[:-1])
            if ';' not in request_key:
                # Prevents adding the main key

                # TODO: should be more modular and testeable...
                continue

            # Get only request part of the redis key
            request_key = request_key.split(';')[-1]
            user_keys.update({request_key})
        return user_keys


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
