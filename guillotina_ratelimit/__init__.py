from guillotina import configure


app_settings = {
    "ratelimit": {
        "global": None,
        "state_manager": "redis",
        "redis_prefix_key": 'ratelimit-'
    }
}

_registered_service_ratelimits = {}


def register_ratelimits(klass, config):
    if klass in _registered_service_ratelimits:
        # do not register twice
        raise Exception('Rate-limit was configured twice!')
    _registered_service_ratelimits[klass] = config


def get_service_ratelimits(method, view_name):
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
        _klass = service['klass']
        _method = service['config']['method']
        _func = service['config']['module']
        _view_name = _klass.__route__.view_name

        if method == _method and view_name == _view_name:
            # Return registered rate limits for corresponding function
            return _registered_service_ratelimits[_func]

    # No configured rate-limits found
    return None


class configure_ratelimits(object):
    def __init__(self, **config):
        self.config = config

    def __call__(self, func):
        register_ratelimits(func, self.config)
        return func


def includeme(root):
    """
    custom application initialization here
    """
    configure.scan('guillotina_ratelimit.subscribers')
    pass
