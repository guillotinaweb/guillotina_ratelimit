from guillotina_ratelimit.state import get_state_manager
from guillotina.utils.auth import get_authenticated_user_id
from guillotina.response import HTTPTooManyRequests
from guillotina import app_settings
from guillotina_ratelimit import get_service_ratelimits


class RateLimitManager:
    def __init__(self, request):
        self.request = request
        self.state_manager = get_state_manager()
        self.user = get_authenticated_user_id(self.request)

    @property
    def request_key(self):
        raise NotImplementedError()

    @property
    def configured_ratelimits(self):
        raise NotImplementedError()

    async def get_current_count(self):
        return await self.state_manager.get_count(
            user=self.user,
            key=self.request_key,
        )

    async def increment(self):
        await self.state_manager.increment(
            user=self.user,
            key=self.request_key,
        )

    async def set_expiration(self, expiration):
        if expiration:
            await self.state_manager.expire_after(
                user=self.user,
                key=self.request_key,
                ttl=expiration,
            )

    async def exceeds_limits(self):
        if not self.configured_ratelimits:
            return False

        limit = self.configured_ratelimits['hits']
        current_count = await self.get_current_count()
        return current_count > limit

    async def get_retry_after(self):
        return await self.state_manager.get_remaining_time(
            user=self.user,
            key=self.request_key,
        )

    def _raise(self):
        raise NotImplementedError()

    async def __call__(self):
        if await self.exceeds_limits():
            retry_after = await self.get_retry_after()
            self._raise(retry_after)
        else:
            # Valid request
            pass


class GlobalRateLimitManager(RateLimitManager):
    @property
    def request_key(self):
        return 'Global'

    @property
    def configured_ratelimits(self):
        return app_settings.get('ratelimit', {}).get('global', None)

    def _raise(self, retry_after):
        resp = HTTPTooManyRequests(content={
            'reason': 'Global rate-limits exceeded'
        })
        resp.headers['Retry-After'] = str(retry_after)
        raise resp


class ServiceRateLimitManager(RateLimitManager):
    @property
    def request_key(self):
        method = self.request.method
        path = self.request.path
        return f'{method} {path}'

    @property
    def configured_ratelimits(self):
        method = self.request.method
        view_name = self.request.view_name
        return get_service_ratelimits(method, view_name)

    def _raise(self, retry_after):
        resp = HTTPTooManyRequests(content={
            'reason': 'Service rate-limits exceeded'
        })
        resp.headers['Retry-After'] = str(retry_after)
        raise resp
