import aiotask_context


async def test_list_rate_limits_returns_correct_counts(container_requester,
                                                       dummy_request,
                                                       global_rate_limits,
):
    aiotask_context.set('request', dummy_request)

    async with container_requester as requester:
        # Make some calls first
        await requester('POST', '/db/guillotina/@foobar?count=1')
        await requester('POST', '/db/guillotina/@foobar?count=2')
        await requester('GET', '/db/guillotina')

        # Get current user rate-limit stats
        resp1, status = await requester('GET', '/db/guillotina/@rate-limits/root')
        assert status == 200
        assert resp1['Global']['count'] == 5
        assert resp1['POST /db/guillotina/@foobar']['count'] == 2

        # Get complete rate-limit
        resp2, status = await requester('GET', '/db/guillotina/@rate-limits')
        assert status == 200
        assert resp2['root']['Global']['count'] == 6
        assert resp2['root']['POST /db/guillotina/@foobar']['count'] == 2

    aiotask_context.set('request', None)
