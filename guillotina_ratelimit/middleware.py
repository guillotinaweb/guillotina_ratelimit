from guillotina_ratelimit.manager import GlobalRateLimitManager
from guillotina_ratelimit.manager import ServiceRateLimitManager


class RateLimitHandler:
    def __init__(self, app, handler):
        self.app = app
        self.handler = handler

    async def __call__(self, request):
        # The following will raise HTTPTooManyRequests if limits are
        # exceeded, and pass otherwise
        await GlobalRateLimitManager(request)()
        await ServiceRateLimitManager(request)()

        resp = await self.handler(request)
        return resp


async def middleware_factory(app, handler):
    return RateLimitHandler(app, handler)
