from guillotina import configure
from guillotina_ratelimit import rate_limit
from guillotina_ratelimit import configure_ratelimits

@configure_ratelimits(seconds=5, hits=2)
@configure.service(name='@foobar', method='POST')
async def foobar(context, request):
    """Dummy endpoint to be used in tests.

    Adds '-foobar' to the title of whatever object is called
    against. Appends a count parameter to ease testing aswell.
    """
    # Get count
    count = request.query['count']
    # Set title
    context.title += f'-foobar-{count}'
    context._p_register()
    # Return it
    return {'title': context.title}
