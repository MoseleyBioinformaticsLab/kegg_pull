import pytest as pt

import kegg_pull.kegg_url as ku


@pt.fixture(autouse=True)
def mock_organism_set(mocker, request):
    if not 'disable_mock_organism_set' in request.keywords:
        organism_set_mock = {'organism-code', 'organism-T-number'}

        mocker.patch.object(
            ku.AbstractKEGGurl, 'organism_set', organism_set_mock
        )
