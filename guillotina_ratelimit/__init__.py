# from guillotina import configure


app_settings = {
    "ratelimit": {
        "global": {
            "seconds": 10,
            "hits": 10,
        },
        "state_manager": "memory",
    }
}


_registered_service_ratelimits = {}


def register_ratelimits(klass, config):
    if klass in _registered_service_ratelimits:
        # do not register twice
        raise Exception('Rate-limit was configured twice!')
    _registered_service_ratelimits[klass] = config


def get_service_ratelimits(klass):
    if klass not in _registered_service_ratelimits:
        return None
    return _registered_service_ratelimits[klass]


class configure_ratelimits(object):
    def __init__(self, **config):
        self.config = config

    def __call__(self, klass):
        register_ratelimits(klass, self.config)
        return klass


def includeme(root):
    """
    custom application initialization here
    """
    # configure.scan('guillotina_ratelimit.api')
    pass
