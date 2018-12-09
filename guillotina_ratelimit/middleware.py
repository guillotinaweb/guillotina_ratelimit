from guillotina_ratelimit.manager import GlobalRateLimitManager
from guillotina_ratelimit.manager import ServiceRateLimitManager
from guillotina.response import HTTPTooManyRequests
from aiohttp import web
import json


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
            resp = web.Response(
                status=ex.status_code,
                body=json.dumps(ex.content),
                content_type='application/json'
            )
            # Set retry-after in headers aswell
            resp.headers['Retry-After'] = ex.headers['Retry-After']
            return resp

        else:
            # Handle response normally
            return await self.handler(request)


async def middleware_factory(app, handler):
    return RateLimitHandler(app, handler)
