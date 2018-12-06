from guillotina_ratelimit.manager import GlobalRateLimitManager
from guillotina_ratelimit.manager import ServiceRateLimitManager


class RateLimitHandler:
    def __init__(self, app, handler):
        self.app = app
        self.handler = handler

    async def __call__(self, request):
        await GlobalRateLimitManager(request).__call__()
        await ServiceRateLimitManager(request).__call__()
        resp = await self.handler(request)
        return resp


async def middleware_factory(app, handler):
    return RateLimitHandler(app, handler)
