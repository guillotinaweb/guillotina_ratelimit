import aiotask_context


async def prepare_rate_limited_endpoint(requester):
    resp, status = await requester('POST', '/db/guillotina', data=json.dumps({
        '@type': 'Item',
        'id': 'foobar-item',
        'title': 'Foobar'
    }))
    assert status in [200, 201]

    # Call endpoint up to rate limit
    for i in range(2):
        resp, status = await requester(
            'POST', f'/db/guillotina/foobar-item/@foobar?count={i}')
        # Check status is correct
        assert status is 200
        assert resp['title'] == f'Foobar-foobar-{i}'

        # Get the item and check title was actually modified
        resp, status = await requester('GET', f'/db/guillotina/foobar-item')
        assert status is 200
        assert resp['title'] == f'Foobar-foobar-{i}'


async def test_response_should_contain_correct_header_and_status(container_requester,
                                                                 dummy_request,
                                                                 redis_enabled):
    aiotask_context.set('request', dummy_request)

    async with container_requester as requester:
        await prepare_rate_limited_endpoint(requester)

        # Call again. We should get rate limited now
        resp, status = await requester(
            'POST', f'/db/guillotina/foobar-item/@foobar?count={i}')
        assert status is 429
        assert resp is 'Too Many Requests'
        retry_after = resp.headers['Retry-After']
        assert isinstance(retry_after, str)
        assert float(retry_after) < 5.0

    aiotask_context.set('request', None)


async def test_endpoint_should_not_be_blocked_after_retry_after(container_requester,
                                                                dummy_request,
                                                                redis_enabled):
    aiotask_context.set('request', dummy_request)

    async with container_requester as requester:
        await prepare_rate_limited_endpoint(requester)

        # Call again. We should get rate limited now
        resp, status = await requester(
            'POST', f'/db/guillotina/foobar-item/@foobar?count={i}')
        assert status is 429
        retry_after = float(resp.headers['Retry-After'])

        # Wait for specified time
        await asyncio.sleep(retry_after)

        # Call again
        resp, status = await requester(
            'POST', '/db/guillotina/foobar-item/@foobar?count=55')
        assert status is 200
        assert resp['title'] == 'Foobar-foobar-55'

    aiotask_context.set('request', None)


async def test_rate_limit_should_block_users_individually(container_requester,
                                                          dummy_request,
                                                          redis_enabled):
    pass
