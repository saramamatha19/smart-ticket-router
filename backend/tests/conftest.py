import pytest

from app.services import router_service


@pytest.fixture(autouse=True)
def _clear_route_ticket_cache():
    """
    route_ticket() is cached (see router_service.py) on the exact
    message text. Several tests reuse generic strings like "a message"
    across different mocked scenarios -- without clearing the cache
    between tests, a later test could silently get an earlier test's
    cached result instead of exercising its own mock.
    """
    router_service.route_ticket.cache_clear()
    yield
    router_service.route_ticket.cache_clear()
