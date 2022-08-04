import pytest as pt


@pt.fixture(autouse=True)
def mock_get_organism_set(mocker, request):
    if not 'disable_mock_get_organism_set' in request.keywords:
        mock_organism_set = {'organism-code', 'organism-T-number'}

        mocker.patch(
            'kegg_pull.kegg_url.AbstractKEGGurl._get_organism_set', return_value=mock_organism_set
        )
