# collective.restapi.searchexpansion

A [plone.restapi](https://github.com/plone/plone.restapi) expansion, `search`, that runs a catalog search and returns its results inside the content response. It saves the second request a client otherwise makes to `@search` after reading a page: whatever the client already knows it will need (other content by path, a listing's results, a folder's children) comes back with the page, and is cached with it.

Many add-ons register an expansion that brings one fixed thing along. This one is generic: the caller says what to search for.

## Request

The search's parameters are `@search`'s own, prefixed with `expand.search.`:

```
GET /some/page?expand=search
    &expand.search.path.query=/footer
    &expand.search.path.query=/shared/banner
    &expand.search.path.depth=0
    &expand.search.fullobjects=1
```

Anything `@search` accepts works the same way: `portal_type`, `sort_on`, `b_size`, `metadata_fields`, `fullobjects`, and so on.

## Response

Under `@components.search`, exactly what `@search` returns for the same query, batching links included:

```json
"@components": {
  "search": {
    "@id": "https://site/some/page/@search?path.query=/footer&...",
    "items": [ { "@id": "https://site/footer", "...": "..." } ],
    "items_total": 2
  }
}
```

Without `expand=search`, the component is only its `@id`, as every expansion is.

The search runs as the requester, through `@search`'s own code, so permissions, batching, `metadata_fields` and `fullobjects` behave exactly as there. Results expand nothing of their own, so a result never runs the search again.

## What it is for

Content the client knows it needs before it makes the request: fixed paths, a known query. Content a page refers to in its own fields is not this expansion's job: the client only knows it once it has the page, and fetches it then.

## Not yet

- One search per request. Several named searches (`expand.search.footer.path.query=…`) are an open question in #1.
- Caching: a response that includes other content goes stale when that content changes. Give responses with `expand=search` a short cache lifetime until there is something better (#1).

## Install

Add the package to your Plone 6.2 site's requirements. Its ZCML loads through `z3c.autoinclude`; there is no profile to install.

## Development

```sh
uv venv
uv pip install -c https://dist.plone.org/release/6.2.3/constraints.txt -e '.[test]'
.venv/bin/pytest
```
