from guillotina_ratelimit.interfaces import IRateLimitManager
from guillotina.component import get_all_utilities_registered_for
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
            # for at least one of the managers are exceeded
            managers = get_all_utilities_registered_for(IRateLimitManager)
            for mgr in managers:
                await mgr(request)

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
