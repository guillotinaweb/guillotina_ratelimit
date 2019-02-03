# guillotina_ratelimit

Provides global and service-specific rate limiting in a per-user
basis.

## Implementation

Essentially, this package provides a subscriber on `IBeforeRenderView`
for every request that triggers the increment of hit request
counters. Additionally, an aiohttp middleware inspects every request
and throws `HTTPTooManyRequest` error responses if a rate limit has
been exceeded.

Both global or service-specific rate limits are checked.

To keep the state of the request counts, the
`IRateLimitingStateManager` utility is provided. Two initial
implementations have been done, one in memory and one using redis,
which can be configured, although the memory implementation is not
recommended for production apps.


## Usage and configuration

To use this addon in your guillotina application you just need to add
a few lines in your config::

``` json
    {
        "applications": ["guillotina_ratelimit"],
        "middlewares": ["guillotina_ratelimit.middleware.middleware_factory"]
    }
```

Global rate limits can be configured in app's settings aswell::

``` json
    app_settings = {
        "ratelimit": {
            "global": {
                "seconds": 10,
                "hits": 500
                },
            "state_manager": "redis",
            "redis_prefix_key": "ratelimit"
        }
    }

```

whereas the `rate_limits` confing key can be used in the
`@configure.service` decorator caon specific services::

``` python
    @configure.service(
        name='@foobar', method='POST',
        rate_limits={
            "seconds": 10,
            "hits": 1,
        }
    )
    async def foobar_endpoint(context, request):
        """
        """
        pass
```

## Possible improvements

- Add user whitelisting to bypass rate-limiting

- Make rate-limits configurable to specific roles

- etc.
