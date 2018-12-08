from guillotina import testing
from guillotina import app_settings
import pytest


base_ratelimit_settings = {
    'state_manager': 'memory',
    'redis_prefix_key': 'ratelimit-',
    # Global rate limits
    'global': {'seconds': 10 * 60 * 60, 'hits': 15},
}


def base_settings_configurator(settings):
    # Install addon and test package
    settings.setdefault('applications', [])
    settings['applications'].extend([
        'guillotina_ratelimit', 'guillotina_ratelimit.tests.package'
    ])

    # Add package custom settings
    settings['ratelimit'] = base_ratelimit_settings

    # Add middleware
    settings.setdefault('middlewares', [])
    settings['middlewares'].append('guillotina_ratelimit.middleware.middleware_factory')


testing.configure_with(base_settings_configurator)


@pytest.fixture('function', params=[
    # {'state_manager': 'redis'},
    {'state_manager': 'memory'},
])
def state_manager(request, redis, dummy_request, loop):
    configured_mgr = request.param.get('state_manager')
    app_settings['ratelimit']['state_manager'] = configured_mgr
    if configured_mgr == 'redis':
        # Redis
        app_settings.update({"redis": {
            'host': redis[0],
            'port': redis[1],
            'pool': {
                "minsize": 1,
                "maxsize": 5,
            },
        }})

        yield redis

        # NOTE: we need to close the redis pool otherwise it's
        # attached to the first loop and the nexts tests have new
        # loops, which causes its to crash
        from guillotina_rediscache.cache import close_redis_pool
        loop.run_until_complete(close_redis_pool())
    else:
        # Memory
        yield
