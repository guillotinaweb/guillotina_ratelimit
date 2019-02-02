from guillotina import configure
from guillotina.interfaces import IBeforeRenderViewEvent
from guillotina.component import get_all_utilities_registered_for
from guillotina_ratelimit.interfaces import IRateLimitManager


@configure.subscriber(for_=IBeforeRenderViewEvent)
async def on_before_view_is_rendered(event):
    """Each rate limit manager takes into account current request
    """
    request = event.request
    managers = get_all_utilities_registered_for(IRateLimitManager)
    for mgr in managers:
        if mgr.request_matches(request):
            await mgr.count_request(request)
