from guillotina import configure
from guillotina.response import HTTPNotFound
from guillotina_ratelimit.state import get_state_manager


@configure.service(
    method='GET', name='@rate-limits/{user_id}',
    permission='guillotina.Manage',
    summary='Returns current rate-limit report for a user')
async def dump_rate_limits(context, request):
    mngr = get_state_manager()
    return await mngr.get_user_rates(request.matchdict['user_id'])


@configure.service(
    method='GET', name='@rate-limits',
    permission='guillotina.Manage',
    summary='Returns the complete rate-limit reports for all users')
async def dump_rate_limits(context, request):
    mngr = get_state_manager()
    return await mngr.get_all_rates()
