from zope.interface import Interface


class IRateLimitingStateManager(Interface):
    """
    Keeps the state about service requests counts on a per-user basis
    """
    async def increment(self, user, key):
        """Increments the request counter for the service key
        """
        pass

    async def get_count(self, user, key):
        """Gets the current request counter for the service key
        """
        pass

    async def expire_after(self, user, key, ttl):
        """Schedules the counter reset for a key after the specified ttl
        """
        pass

    async def get_remaining_time(self, user, key):
        """Gets the remaining time until the counter is reset
        """
        pass

    async def get_user_rates(self, user):
        """Returns the current rates for a given user
        """
        pass

    async def get_all_rates(self):
        """Returns the complete rate limits state for the application
        """
        pass
