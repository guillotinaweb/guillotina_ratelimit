from guillotina import configure
from guillotina.interfaces import IAfterTraversalEvent
from guillotina.interfaces import IAfterAuthenticationEvent
from guillotina_ratelimit.state import get_ratelimit_state_manager
from guillotina_ratelimit.manager import GlobalRateLimitManager
from guillotina_ratelimit.manager import ServiceRateLimitManager


@configure.subscriber(for_=IAfterTraversalEvent)
async def on_after_traversal(event):
    """Increment rate limit counters for request
    """
    request = event.request

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
