import pytest as pt


@pt.fixture(autouse=True)
def mock_organism_set(mocker, request):
    if not 'disable_mock_organism_set' in request.keywords:
        organism_set_mock = {'organism-code', 'organism-T-number'}

        mocker.patch(
            'kegg_pull.kegg_url.AbstractKEGGurl.organism_set', return_value=organism_set_mock
        )
