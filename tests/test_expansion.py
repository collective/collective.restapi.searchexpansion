"""`?expand=search` runs `@search` with the `expand.search.`-prefixed
parameters and returns what `@search` returns, under `@components.search`."""

from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession

import pytest
import transaction


@pytest.fixture
def site(functional):
    portal = functional["portal"]
    with api.env.adopt_roles(["Manager"]):
        page = api.content.create(
            container=portal, type="Document", id="page", title="Page"
        )
        api.content.transition(obj=page, transition="publish")
        shared = api.content.create(
            container=portal, type="Folder", id="shared", title="Shared"
        )
        for id_, title in (
            ("footer", "Footer"),
            ("banner", "Banner"),
            ("other", "Other"),
        ):
            doc = api.content.create(
                container=shared, type="Document", id=id_, title=title
            )
            api.content.transition(obj=doc, transition="publish")
        api.content.create(container=shared, type="Document", id="draft", title="Draft")
    transaction.commit()
    return portal


@pytest.fixture
def anonymous(site):
    session = RelativeSession(site.absolute_url())
    session.headers.update({"Accept": "application/json"})
    yield session
    session.close()


@pytest.fixture
def editor(site):
    session = RelativeSession(site.absolute_url())
    session.headers.update({"Accept": "application/json"})
    session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
    yield session
    session.close()


def titles(result):
    return sorted(item["title"] for item in result["items"])


def test_it_returns_what_search_returns(site, anonymous):
    params = {"path.query": "/plone/shared", "portal_type": "Document", "sort_on": "id"}
    page = anonymous.get(
        "page",
        params={
            "expand": "search",
            **{f"expand.search.{k}": v for k, v in params.items()},
        },
    ).json()
    search = anonymous.get("@search", params=params).json()
    expanded = page["@components"]["search"]
    assert expanded["items"] == search["items"]
    assert expanded["items_total"] == search["items_total"] == 3
    assert expanded["@id"] == search["@id"].replace(
        site.absolute_url(), f"{site.absolute_url()}/page"
    )


def test_without_expand_it_is_only_its_id(site, anonymous):
    page = anonymous.get("page").json()
    assert page["@components"]["search"] == {
        "@id": f"{site.absolute_url()}/page/@search"
    }


def test_it_runs_as_the_requester(site, anonymous, editor):
    params = {
        "expand": "search",
        "expand.search.path.query": "/plone/shared",
        "expand.search.portal_type": "Document",
    }
    assert titles(
        anonymous.get("page", params=params).json()["@components"]["search"]
    ) == ["Banner", "Footer", "Other"]
    assert titles(
        editor.get("page", params=params).json()["@components"]["search"]
    ) == ["Banner", "Draft", "Footer", "Other"]


def test_full_objects_do_not_search_again(site, anonymous):
    result = anonymous.get(
        "page",
        params={
            "expand": "search",
            "expand.search.path.query": "/plone/shared/footer",
            "expand.search.fullobjects": "1",
        },
    ).json()["@components"]["search"]
    (footer,) = result["items"]
    assert footer["title"] == "Footer"
    assert "items" not in footer["@components"]["search"]


def test_several_paths_return_exactly_those_items(site, anonymous):
    result = anonymous.get(
        "page",
        params=[
            ("expand", "search"),
            ("expand.search.path.query", "/plone/shared/footer"),
            ("expand.search.path.query", "/plone/shared/banner"),
            ("expand.search.path.depth", "0"),
        ],
    ).json()["@components"]["search"]
    assert titles(result) == ["Banner", "Footer"]


def test_batching_is_the_search_s_own(site, anonymous):
    result = anonymous.get(
        "page",
        params={
            "expand": "search",
            "expand.search.path.query": "/plone/shared",
            "expand.search.portal_type": "Document",
            "expand.search.b_size": "2",
            "expand.search.sort_on": "id",
        },
    ).json()["@components"]["search"]
    assert len(result["items"]) == 2
    assert result["items_total"] == 3
    assert result["batching"]["next"].startswith(f"{site.absolute_url()}/page/@search?")


def test_the_page_itself_is_unaffected(site, anonymous):
    plain = anonymous.get("page").json()
    expanded = anonymous.get(
        "page", params={"expand": "search", "expand.search.path.query": "/plone/shared"}
    ).json()
    del plain["@components"], expanded["@components"]
    assert expanded == plain
