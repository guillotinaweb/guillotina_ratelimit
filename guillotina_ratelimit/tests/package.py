from guillotina import configure

SERVICE_RATE_LIMITS = {
    'seconds': 2,
    'hits': 2
}


@configure.service(
    name='@foobar', method='POST',
    rate_limits=SERVICE_RATE_LIMITS)
async def foobar(context, request):
    """
    Dummy endpoint to be used in tests.

    Adds '-foobar' to the title of whatever object is called
    against. Appends a count parameter to ease testing aswell.
    """
    # Get count
    count = request.query['count']
    # Set title
    context.title += f'-{count}'
    context._p_register()
    # Return it
    return {'title': context.title}


@configure.service(
    name='@foobar2', method='GET',
    rate_limits=SERVICE_RATE_LIMITS)
async def foobar2(context, request):
    """
    Dummy endpoint to be used in tests.
    """
    return {}
