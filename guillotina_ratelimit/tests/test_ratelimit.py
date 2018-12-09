from guillotina_ratelimit.tests.package import SERVICE_RATE_LIMITS
import aiotask_context
import json
import asyncio


async def test_global_rate_limits(container_requester, dummy_request,
                                  state_manager, global_rate_limits):
    aiotask_context.set('request', dummy_request)

    retry_after = None
    async with container_requester as requester:
        for i in range(global_rate_limits['hits'] + 1):
            resp, status, headers = await requester.make_request(
                'GET', '/db/guillotina')
            if status not in (200, 201):
                # Check status, content and headers
                assert status == 429
                assert resp['reason'] == 'Global rate-limits exceeded'
                retry_after = float(headers['Retry-After'])
                assert retry_after < global_rate_limits['seconds']
                break

        assert i == global_rate_limits['hits']

        # Wait for rate-limit counters to be reset
        assert retry_after
        await asyncio.sleep(retry_after)

    aiotask_context.set('request', None)


async def prepare_rate_limited_endpoint(requester):
    # Create item
    resp, status = await requester('POST', '/db/guillotina', data=json.dumps({
        '@type': 'Item',
        'id': 'foobar-item',
        'title': 'Foobar'
    }))
    assert status in [200, 201]

    # Call endpoint up to rate limit
    for i in range(SERVICE_RATE_LIMITS['hits']):
        resp, status = await requester(
            'POST', f'/db/guillotina/foobar-item/@foobar?count={i}')
        # Check status is correct
        assert status == 200
        assert str(i) in resp['title']

        # Get the item and check title was actually modified
        resp, status = await requester('GET', f'/db/guillotina/foobar-item')
        assert status == 200
        assert str(i) in resp['title']

    aiotask_context.set('request', None)


async def test_service_rate_limits(container_requester, dummy_request,
                                   state_manager):
    aiotask_context.set('request', dummy_request)

    async with container_requester as requester:
        await prepare_rate_limited_endpoint(requester)

        # Call again. We should get rate limited now
        resp, status, headers = await requester.make_request(
            'POST', '/db/guillotina/foobar-item/@foobar?count=55')
        # Check status, content and headers
        assert status == 429
        assert resp['reason'] == 'Service rate-limits exceeded'
        retry_after = float(headers['Retry-After'])
        assert retry_after < SERVICE_RATE_LIMITS['seconds']

        # Wait for retry_after and check that it works
        await asyncio.sleep(retry_after)
        resp, status = await requester(
            'POST', '/db/guillotina/foobar-item/@foobar?count=55')
        assert status == 200

    aiotask_context.set('request', None)
