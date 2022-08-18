import pytest as pt
import requests as rq

import kegg_pull.kegg_url as ku
import tests.utils as u


# TODO Test other URL _validate methods
test_validate_data = [
    (
        ku.ListKEGGurl, {'database_name': 'invalid-database-name'},
        'Invalid database name: "invalid-database-name". Valid values are: <org>, ag, brite, compound, dgroup, disease,'
        ' drug, enzyme, genome, glycan, ko, module, network, organism, pathway, rclass, reaction, variant, vg, vp'
    ),
    (
        ku.InfoKEGGurl, {'database_name': 'organism'},
        'Invalid database name: "organism". Valid values are: <org>, ag, brite, compound, dgroup, disease, drug, '
        'enzyme, genome, glycan, ko, module, network, pathway, rclass, reaction, variant, vg, vp'
    ),
    (
        ku.GetKEGGurl, {'entry_ids': [], 'entry_field': None}, 'Entry IDs must be specified for the KEGG get operation'
    ),
    (
        ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': 'invalid-entry-field'},
        'Invalid KEGG entry field: "invalid-entry-field". Valid values are: aaseq, conf, image, json, kcf, kgml, mol, '
        'ntseq'
    ),
    (
        ku.GetKEGGurl, {'entry_ids': ['x', 'y'], 'entry_field': 'json'},
        'The KEGG entry field: "json" only supports requests of one KEGG entry at a time but 2 entry IDs are provided'
    ),
    (
        ku.GetKEGGurl, {'entry_ids': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']},
        f'The maximum number of entry IDs is {ku.GetKEGGurl.MAX_ENTRY_IDS_PER_URL} but 11 were provided'
    )
]
@pt.mark.parametrize('KEGGurl,kwargs,expected_message', test_validate_data)
def test_validate(KEGGurl: type, kwargs: dict, expected_message: str):
    with pt.raises(ValueError) as error:
        KEGGurl(**kwargs)

    expected_message = f'Cannot create URL - {expected_message}'
    u.assert_expected_error_message(expected_message=expected_message, error=error)


# TODO Test other URL _create_rest_options methods
test_create_rest_options_data = [
    (ku.ListKEGGurl, {'database_name': 'vg'}, 'list', 'vg'),
    (ku.ListKEGGurl, {'database_name': 'organism-code'}, 'list', 'organism-code'),
    (ku.ListKEGGurl, {'database_name': 'organism'}, 'list', 'organism'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': None}, 'get', 'x'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': 'image'}, 'get', 'x/image'),
    (ku.GetKEGGurl, {'entry_ids': ['x'], 'entry_field': 'aaseq'}, 'get', 'x/aaseq'),
    (ku.GetKEGGurl, {'entry_ids': ['x', 'y'], 'entry_field': None}, 'get', 'x+y'),
    (ku.GetKEGGurl, {'entry_ids': ['x', 'y', 'z'], 'entry_field': 'ntseq'}, 'get', 'x+y+z/ntseq')
]
@pt.mark.parametrize('KEGGurl,kwargs,api_operation,rest_options', test_create_rest_options_data)
def test_create_rest_options(KEGGurl: type, kwargs: dict, api_operation: str, rest_options: str):
    kegg_url: ku.AbstractKEGGurl = KEGGurl(**kwargs)
    expected_url = f'{ku.BASE_URL}/{api_operation}/{rest_options}'

    assert str(kegg_url) == kegg_url.url == expected_url

    if KEGGurl == ku.GetKEGGurl:
        assert kegg_url.__getattribute__('multiple_entry_ids') == (len(kegg_url.__getattribute__('entry_ids')) > 1)


@pt.fixture(name='_')
def reset_organism_set():
    ku.AbstractKEGGurl._organism_set = None


@pt.mark.disable_mock_organism_set
def test_organism_set(mocker, _):
    mock_text = """
        T06555	psyt	Candidatus Prometheoarchaeum syntrophicum	Prokaryotes;Archaea;Lokiarchaeota;Prometheoarchaeum
        T03835	agw	Archaeon GW2011_AR10	Prokaryotes;Archaea;unclassified Archaea
        T03843	arg	Archaeon GW2011_AR20	Prokaryotes;Archaea;unclassified Archaea
    """

    mock_response = mocker.MagicMock(status_code=200, text=mock_text)
    mock_get: mocker.MagicMock = mocker.patch('kegg_pull.kegg_url.rq.get', return_value=mock_response)
    actual_organism_set = ku.AbstractKEGGurl.organism_set
    mock_get.assert_called_once_with(url=f'{ku.BASE_URL}/list/organism', timeout=60)
    expected_organism_set = {'agw', 'T03835', 'T06555', 'T03843', 'psyt', 'arg'}

    assert actual_organism_set == expected_organism_set

    mock_get.reset_mock()
    actual_organism_set = ku.AbstractKEGGurl.organism_set
    mock_get.assert_not_called()

    assert actual_organism_set == expected_organism_set


@pt.mark.parametrize('timeout', [True, False])
@pt.mark.disable_mock_organism_set
def test_organism_set_unsuccessful(mocker, timeout: bool, _):
    get_function_patch_path = 'kegg_pull.kegg_url.rq.get'
    url = f'{ku.BASE_URL}/list/organism'
    error_message = 'The request to the KEGG web API {} while fetching the organism set using the URL: {}'

    if timeout:
        get_mock: mocker.MagicMock = mocker.patch(get_function_patch_path, side_effect=rq.exceptions.Timeout())
        error_message: str = error_message.format('timed out', url)
    else:
        failed_status_code = 404

        get_mock: mocker.MagicMock = mocker.patch(
            get_function_patch_path, return_value=mocker.MagicMock(status_code=failed_status_code)
        )

        error_message: str = error_message.format(f'failed with status code {failed_status_code}', url)

    with pt.raises(RuntimeError) as error:
        # noinspection PyStatementEffect
        ku.AbstractKEGGurl.organism_set

    get_mock.assert_called_once_with(url=url, timeout=60)
    u.assert_expected_error_message(expected_message=error_message, error=error)


test_create_url_data = [
    ('ListKEGGurl', ku.UrlType.LIST),
    ('InfoKEGGurl', ku.UrlType.INFO),
    ('GetKEGGurl', ku.UrlType.GET),
    ('KeywordsFindKEGGurl', ku.UrlType.KEYWORDS_FIND),
    ('MolecularFindKEGGurl', ku.UrlType.MOLECULAR_FIND),
    ('DatabaseConvKEGGurl', ku.UrlType.DATABASE_CONV),
    ('EntriesConvKEGGurl', ku.UrlType.ENTRIES_CONV),
    ('DatabaseLinkKEGGurl', ku.UrlType.DATABASE_LINK),
    ('EntriesLinkKEGGurl', ku.UrlType.ENTRIES_LINK),
    ('DdiKEGGurl', ku.UrlType.DDI)
]
@pt.mark.parametrize('class_name,url_type', test_create_url_data)
def test_create_url(mocker, class_name: str, url_type: ku.UrlType):
    kegg_url_mock = mocker.MagicMock()
    KEGGurlMock = mocker.patch(f'kegg_pull.kegg_url.{class_name}', return_value=kegg_url_mock)
    kwargs_mock = {'param': 'arg'}
    kegg_url = ku.create_url(url_type=url_type, **kwargs_mock)
    KEGGurlMock.assert_called_once_with(**kwargs_mock)

    assert kegg_url == kegg_url_mock
