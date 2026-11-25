"""The `search` expansion: `@search`, run inside the content response."""

from contextlib import contextmanager
from plone.restapi.interfaces import IExpandableElement
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from urllib.parse import parse_qsl
from urllib.parse import urlencode
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface


PREFIX = "expand.search."


@contextmanager
def as_search_request(request, url: str, form: dict, query_string: str):
    """Make `request` look like a GET of `url` with `form`, for as long as the
    search runs. `@search` reads its batching from the form and builds its links
    from ACTUAL_URL and QUERY_STRING; and with the page's own `expand` out of
    the form, the results expand nothing of their own, this search included."""
    saved = (
        request.form,
        request.other.get("ACTUAL_URL"),
        request.environ.get("QUERY_STRING"),
    )
    request.form = form
    request.other["ACTUAL_URL"] = url
    request.environ["QUERY_STRING"] = query_string
    try:
        yield
    finally:
        request.form, request.other["ACTUAL_URL"], request.environ["QUERY_STRING"] = (
            saved
        )


@implementer(IExpandableElement)
@adapter(Interface, Interface)
class SearchExpansion:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self, expand: bool = False) -> dict:
        url = f"{self.context.absolute_url()}/@search"
        if not expand:
            return {"search": {"@id": url}}
        form = {
            key[len(PREFIX) :]: value
            for key, value in self.request.form.items()
            if key.startswith(PREFIX)
        }
        query_string = urlencode([
            (key[len(PREFIX) :], value)
            for key, value in parse_qsl(
                self.request.environ.get("QUERY_STRING", ""), keep_blank_values=True
            )
            if key.startswith(PREFIX)
        ])
        with as_search_request(self.request, url, form, query_string):
            query = unflatten_dotted_dict(dict(form))
            result = SearchHandler(self.context, self.request).search(query)
        return {"search": result}
