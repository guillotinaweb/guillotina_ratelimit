from guillotina import configure


app_settings = {
    "ratelimit": {
        "global": None,
        "state_manager": "redis",
        "redis_prefix_key": 'ratelimit-'
    }
}


_service_rate_limits_cache = {}


def get_service_ratelimits(method, view_name):
    if (method, view_name) not in _service_rate_limits_cache:
        rate_limits = _get_service_ratelimits(method, view_name)
        # Cache them forever
        _service_rate_limits_cache[(method, view_name)] = rate_limits
        return rate_limits

    return _service_rate_limits_cache[(method, view_name)]


def _get_service_ratelimits(method, view_name):
    if not view_name:
        # Not a service. Will be dealt with on global rate limits
        return None

    # Get app registered services from configuration
    _guillotina_services = [
        s for s in configure._registered_configurations
        if 'service' in s
    ]

    # Iterate them and look for a match
    for (_, service) in _guillotina_services:
        if 'rate_limits' not in service['config']:
            # No rate limits configured
            continue

        _method = service['config']['method']
        _view_name = service['klass'].__route__.view_name
        if method == _method and view_name == _view_name:
            # Return registered rate limits for corresponding function
            return service['config'].get('rate_limits', None)

    # No configured rate-limits found
    return None


def includeme(root):
    """
    custom application initialization here
    """
    configure.scan('guillotina_ratelimit.api')
    configure.scan('guillotina_ratelimit.manager')
    configure.scan('guillotina_ratelimit.subscribers')
