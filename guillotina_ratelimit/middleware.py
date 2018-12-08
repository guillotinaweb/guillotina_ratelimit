from guillotina_ratelimit.manager import GlobalRateLimitManager
from guillotina_ratelimit.manager import ServiceRateLimitManager
from guillotina.response import HTTPTooManyRequests
from aiohttp import web


class RateLimitHandler:
    def __init__(self, app, handler):
        self.app = app
        self.handler = handler

    async def __call__(self, request):

        try:
            # The following will raise HTTPTooManyRequests if limits
            # are exceeded
            await GlobalRateLimitManager(request).__call__()
            await ServiceRateLimitManager(request).__call__()

        except HTTPTooManyRequests as ex:  # noqa
            # TODO: investigate how to correctly return another
            # response from within an aiohttp middleware
            return web.Response(
                status=429,
            )
        else:
            # Handle response normally
            return await self.handler(request)


async def middleware_factory(app, handler):
    return RateLimitHandler(app, handler)
