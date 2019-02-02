from guillotina import configure
from guillotina.component import get_all_utilities_registered_for
from guillotina_ratelimit.interfaces import IRateLimitManager
from guillotina.utils.auth import get_authenticated_user_id


@configure.service(
    method='GET', name='@ratelimits',
    permission='guillotina.AccessContent',
    summary='Returns a report of current rate limits for the user')
async def get_ratelimits_report(context, request):
    user = get_authenticated_user_id(request)

    report = {}

    # Iterate registered rate limit managers
    managers = get_all_utilities_registered_for(IRateLimitManager)
    for mgr in managers:
        mgr_report = await mgr.get_user_report(user)
        report.update(mgr_report)

    return report
