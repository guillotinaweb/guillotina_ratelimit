from guillotina_ratelimit.tests.package import SERVICE_RATE_LIMITS
import aiotask_context


async def test_get_ratelimits_report(
    container_requester,
    dummy_request,
    state_manager,
    global_rate_limits,
):
    aiotask_context.set('request', dummy_request)

    async with container_requester as requester:
        # Make a request first
        _, status = await requester('GET', '/db/guillotina/@foobar2')
        assert status == 200

        # Check report
        report, status = await requester('GET', '/db/guillotina/@ratelimits')
        assert status == 200

        # Check service manager report
        service_key = 'GET /db/guillotina/@foobar2'
        assert service_key in report
        assert report[service_key]['count'] == 1
        assert 0 < report[service_key]['remaining'] < SERVICE_RATE_LIMITS['seconds']

        # Check global managere report
        global_key = 'Global'
        assert global_key in report
        assert report[global_key]['count'] == 3
        assert 0 < report[global_key]['remaining'] < global_rate_limits['seconds']

    aiotask_context.set('request', None)
