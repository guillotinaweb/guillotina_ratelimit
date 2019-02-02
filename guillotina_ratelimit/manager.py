from guillotina_ratelimit.state import get_state_manager
from guillotina.utils.auth import get_authenticated_user_id
from guillotina.response import HTTPTooManyRequests
from guillotina import app_settings
from guillotina import configure
from guillotina_ratelimit import get_service_ratelimits
from guillotina_ratelimit.interfaces import IRateLimitManager


class RateLimitManager:
    def __init__(self):
        self.state_manager = get_state_manager()

    def configured_ratelimits(self, request):
        raise NotImplementedError()

    def request_hits_limit(self, request):
        raise NotImplementedError()

    async def get_current_count(self, user, request_key):
        return await self.state_manager.get_count(user, request_key)

    async def increment(self, user, request_key):
        await self.state_manager.increment(user, request_key)

    async def set_expiration(self, user, request_key, expiration=None):
        if expiration:
            await self.state_manager.expire_after(user, request_key,
                                                  ttl=expiration)

    async def exceeds_limits(self, request):
        if not self.configured_ratelimits(request):
            # Can't exceed unexisting configured limits
            return False

        # Get max allowed request hits
        max_hits = self.request_hits_limit(request)
        if not max_hits:
            # No max hits configured
            return False

        user = get_authenticated_user_id(request)
        request_key = self.request_key(request)
        current_count = await self.get_current_count(user, request_key)

        return current_count and current_count > max_hits

    async def get_retry_after(self, user, request_key):
        return await self.state_manager.get_remaining_time(user, request_key)

    async def count_request(self, request):
        user = get_authenticated_user_id(request)
        request_key = self.request_key(request)
        initial_count = await self.get_current_count(user, request_key)
        await self.increment(user, request_key)
        if not initial_count:
            # Set expiration if needed
            crl = self.configured_ratelimits(request)
            await self.set_expiration(user, request_key, expiration=crl['seconds'])

    def _raise(self, retry_after):
        raise NotImplementedError()

    async def get_user_report(self, user):
        return await self.state_manager.dump_user_counts(user)

    async def __call__(self, request):
        if not await self.exceeds_limits(request):
            # Valid request
            return

        # Raise exception
        user = get_authenticated_user_id(request)
        request_key = self.request_key(request)
        retry_after = await self.get_retry_after(user, request_key)
        self._raise(retry_after)


@configure.utility(provides=IRateLimitManager, name='global')
class GlobalRateLimitManager(RateLimitManager):

    def request_key(self, request):
        # Use same key for all requests
        return 'Global'

    def request_hits_limit(self, request):
        crl = self.configured_ratelimits(request)
        if not crl:
            return None
        return crl['hits']

    def configured_ratelimits(self, request):
        return app_settings.get('ratelimit', {}).get('global', None)

    def _raise(self, retry_after):
        resp = HTTPTooManyRequests(content={
            'reason': 'Global rate-limits exceeded',
            'Retry-After': retry_after,
        })
        resp.headers['Retry-After'] = str(retry_after)
        raise resp

    def request_matches(self, request):
        # Return true only if global rate limits are
        if self.configured_ratelimits(request):
            return True
        return False


@configure.utility(provides=IRateLimitManager, name='service')
class ServiceRateLimitManager(RateLimitManager):

    def request_key(self, request):
        method = request.method
        path = request.path
        return f'{method} {path}'

    def request_hits_limit(self, request):
        crl = self.configured_ratelimits(request)
        if not crl:
            return None
        return crl['hits'] - 1

    def configured_ratelimits(self, request):
        method = request.method
        view_name = request.view_name
        return get_service_ratelimits(method, view_name)

    def _raise(self, retry_after):
        resp = HTTPTooManyRequests(content={
            'reason': 'Service rate-limits exceeded',
            'Retry-After': retry_after,
        })
        resp.headers['Retry-After'] = str(retry_after)
        raise resp

    def request_matches(self, request):
        # Check that it is actually a service
        if not request.view_name:
            return False

        # Check there are configured rate limits for this service
        if not self.configured_ratelimits(request):
            return False

        return True
