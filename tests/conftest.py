"""plone.restapi's own test site, with this package's ZCML, served over HTTP."""

from plone.app.testing import FunctionalTesting
from plone.app.testing import PloneSandboxLayer
from plone.restapi.testing import PLONE_RESTAPI_DX_FIXTURE
from plone.testing.zope import WSGI_SERVER_FIXTURE
from pytest_plone import fixtures_factory


class Layer(PloneSandboxLayer):
    defaultBases = (PLONE_RESTAPI_DX_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import collective.restapi.searchexpansion

        self.loadZCML(package=collective.restapi.searchexpansion)

    def setUpPloneSite(self, portal):
        portal.portal_workflow.setChainForPortalTypes(
            ("Document",), ("simple_publication_workflow",)
        )


FIXTURE = Layer()

FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(FIXTURE, WSGI_SERVER_FIXTURE), name="SearchExpansion:Functional"
)


pytest_plugins = ["pytest_plone"]


globals().update(fixtures_factory(((FUNCTIONAL_TESTING, "functional"),)))
