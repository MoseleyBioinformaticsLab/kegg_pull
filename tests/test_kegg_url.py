import pytest as pt

import kegg_pull.kegg_url as ku
import tests.utils as u


def test_list_kegg_url_validate():
    with pt.raises(ValueError) as e:
        ku.ListKEGGurl(database_name='invalid-database-name')

    u.assert_expected_error_message(
        expected_message='Cannot create URL - Invalid database name: "invalid-database-name". Valid values are: ag, '
                         'brite, compound, dgroup, disease, drug, enzyme, genome, glycan, ko, module, network, '
                         'pathway, rclass, reaction, variant, vg, vp', e=e
    )


# TODO test with database_name="organism"
# TODO test with database_name=<org>
def test_list_kegg_url_create_url_options():
    list_kegg_url = ku.ListKEGGurl(database_name='vg')
    expected_url = f'{ku.BASE_URL}/list/vg'

    assert str(list_kegg_url) == list_kegg_url.url == expected_url


test_get_kegg_url_validate_data = [
    ([], None, 'Cannot create URL - Entry IDs must be specified for the KEGG get operation'),
    (
        ['x'], 'invalid-entry-field', 'Cannot create URL - Invalid KEGG entry field: "invalid-entry-field". Valid '
                                      'values are: aaseq, conf, image, json, kcf, kgml, mol, ntseq'
    ),
    (
        ['x', 'y'], 'json', 'Cannot create URL - The KEGG entry field: "json" only supports requests of one KEGG entry '
                            'at a time but 2 entry IDs are provided'
    )
]


@pt.mark.parametrize('entry_ids,entry_field,expected_error_message', test_get_kegg_url_validate_data)
def test_get_kegg_url_validate(entry_ids: list, entry_field: str, expected_error_message: str):
    with pt.raises(ValueError) as e:
        ku.GetKEGGurl(entry_ids=entry_ids, entry_field=entry_field)

    u.assert_expected_error_message(expected_message=expected_error_message, e=e)


test_get_kegg_url_create_url_options_data: list = [
    (['x'], None, 'get/x'),
    (['x'], 'image', 'get/x/image'),
    (['x'], 'aaseq', 'get/x/aaseq'),
    (['x', 'y'], None, 'get/x+y'),
    (['x', 'y', 'z'], 'ntseq', 'get/x+y+z/ntseq')
]


@pt.mark.parametrize('entry_ids,entry_field,expected_url', test_get_kegg_url_create_url_options_data)
def test_get_kegg_url_create_url_options(entry_ids: list, entry_field: str, expected_url: str):
    get_kegg_url = ku.GetKEGGurl(entry_ids=entry_ids, entry_field=entry_field)
    expected_url = f'{ku.BASE_URL}/{expected_url}'

    assert get_kegg_url.url == expected_url


# TODO test with fail and timeout
@pt.mark.disable_mock_get_organism_set
def test_get_organism_list(mocker):
    mock_text = """
        T06555	psyt	Candidatus Prometheoarchaeum syntrophicum	Prokaryotes;Archaea;Lokiarchaeota;Prometheoarchaeum
        T03835	agw	Archaeon GW2011_AR10	Prokaryotes;Archaea;unclassified Archaea
        T03843	arg	Archaeon GW2011_AR20	Prokaryotes;Archaea;unclassified Archaea
    """

    mock_response = mocker.MagicMock(status_code=200, text=mock_text)
    mock_get: mocker.MagicMock = mocker.patch('kegg_pull.kegg_url.rq.get', return_value=mock_response)

    # noinspection PyUnresolvedReferences
    actual_organism_set = ku.AbstractKEGGurl._get_organism_set()
    mock_get.assert_called_once_with(url=f'{ku.BASE_URL}/list/organism', timeout=60)
    expected_organism_set = {'agw', 'T03835', 'T06555', 'T03843', 'psyt', 'arg'}

    assert actual_organism_set == expected_organism_set

# TODO Test other URLs
