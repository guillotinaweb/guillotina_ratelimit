from guillotina import configure
from guillotina.interfaces import IBeforeRenderViewEvent
from guillotina_ratelimit.manager import GlobalRateLimitManager
from guillotina_ratelimit.manager import ServiceRateLimitManager


@configure.subscriber(for_=IBeforeRenderViewEvent)
async def on_before_view_is_rendered(event):
    """Increment rate limit counters for request
    """
    request = event.request
    view = event.view

    # For both global and per-service
    _global = GlobalRateLimitManager(request)
    _service = ServiceRateLimitManager(request)
    for mgr in (_global, _service):
        initial_count = await mgr.get_current_count()
        await mgr.increment()
        if not initial_count:
            # Set expiration if needed
            expiration = mgr.configured_ratelimits['seconds']
            await mgr.set_expiration(expiration)
