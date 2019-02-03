from guillotina_ratelimit.state import get_state_manager
import asyncio


async def clear_cache(sm):
    await sm._clean()


async def test_increment_should_increment(state_manager, loop):
    sm = get_state_manager(loop)

    # Check initial count == 0
    assert await sm.get_count('user', '@foobar') == 0

    # Check it increments by one at a time
    for i in range(3):
        await sm.increment('user', '@foobar', i)
        assert await sm.get_count('user', '@foobar') == i + 1

    await clear_cache(sm)


async def test_increment_should_count_per_user(state_manager, loop):
    sm = get_state_manager(loop)

    assert await sm.get_count('user1', '@foobar') == 0
    assert await sm.get_count('user2', '@foobar') == 0

    await sm.increment('user1', '@foobar', 1)
    await sm.increment('user1', '@foobar', 2)

    await sm.increment('user2', '@foobar', 3)

    assert await sm.get_count('user1', '@foobar') == 2
    assert await sm.get_count('user2', '@foobar') == 1

    await clear_cache(sm)


async def test_expire_after_should_reset_counter(state_manager, loop):
    sm = get_state_manager(loop)

    assert await sm.get_count('user', '@foobar') == 0
    await sm.increment('user', '@foobar', 1)
    await sm.expire_after('user', '@foobar', 1, 2)

    await sm.increment('user', '@foobar', 2)
    await sm.expire_after('user', '@foobar', 2, 2)

    assert await sm.get_count('user', '@foobar') == 2
    await asyncio.sleep(3)
    assert await sm.get_count('user', '@foobar') == 0

    await clear_cache(sm)


async def test_expire_after_should_reset_per_user_and_per_endpoint(state_manager, loop):
    sm = get_state_manager(loop)

    assert await sm.get_count('user1', '@foobar1') == 0
    assert await sm.get_count('user1', '@foobar2') == 0
    assert await sm.get_count('user2', '@foobar1') == 0
    assert await sm.get_count('user2', '@foobar2') == 0

    # Add at least one count for each pair
    await sm.increment('user1', '@foobar1', 1)
    await sm.increment('user1', '@foobar2', 2)
    await sm.increment('user2', '@foobar1', 3)
    await sm.increment('user2', '@foobar2', 4)

    # Set different expirations for each user-endpoint pair
    await sm.expire_after('user1', '@foobar1', 1, ttl=1)
    await sm.expire_after('user1', '@foobar2', 2, ttl=2)
    await sm.expire_after('user2', '@foobar1', 3, ttl=3)
    await sm.expire_after('user2', '@foobar2', 4, ttl=4)

    # Sleep 1 and check only one counter has been reset
    await asyncio.sleep(1.1)
    assert await sm.get_count('user1', '@foobar1') == 0
    assert await sm.get_count('user1', '@foobar2') == 1
    assert await sm.get_count('user2', '@foobar1') == 1
    assert await sm.get_count('user2', '@foobar2') == 1

    await asyncio.sleep(1)
    assert await sm.get_count('user1', '@foobar1') == 0
    assert await sm.get_count('user1', '@foobar2') == 0
    assert await sm.get_count('user2', '@foobar1') == 1
    assert await sm.get_count('user2', '@foobar2') == 1

    await asyncio.sleep(1)
    assert await sm.get_count('user1', '@foobar1') == 0
    assert await sm.get_count('user1', '@foobar2') == 0
    assert await sm.get_count('user2', '@foobar1') == 0
    assert await sm.get_count('user2', '@foobar2') == 1

    # All should be expired by now
    await asyncio.sleep(1)
    assert await sm.get_count('user1', '@foobar1') == 0
    assert await sm.get_count('user1', '@foobar2') == 0
    assert await sm.get_count('user2', '@foobar1') == 0
    assert await sm.get_count('user2', '@foobar2') == 0

    await clear_cache(sm)


async def test_get_remaining_time(state_manager, loop):
    sm = get_state_manager(loop)

    assert await sm.get_count('user', '@foobar') == 0
    await sm.increment('user', '@foobar', 1)
    await sm.increment('user', '@foobar', 2)

    expire_after = 3
    remaining = 3
    await sm.expire_after('user', '@foobar', 1, expire_after)
    await sm.expire_after('user', '@foobar', 2, expire_after)

    while True:
        await asyncio.sleep(0.5)
        new_remaining = await sm.get_remaining_time('user', '@foobar')
        if new_remaining == 0:
            break

        assert new_remaining < remaining
        remaining = new_remaining

    await clear_cache(sm)


async def test_dump_user_counts(state_manager, loop):
    sm = get_state_manager(loop)

    assert await sm.get_count('user', '@foobar') == 0
    await sm.increment('user', '@foobar', 1)
    await sm.increment('user', '@foobar', 2)
    await sm.expire_after('user', '@foobar', 1, 10)
    await sm.expire_after('user', '@foobar', 2, 10)
    assert await sm.get_count('user', '@foobar') == 2

    report = await sm.dump_user_counts('user')
    assert '@foobar' in report
    assert report['@foobar']['count'] == 2
    assert 0 < report['@foobar']['count'] < 10

    await clear_cache(sm)
