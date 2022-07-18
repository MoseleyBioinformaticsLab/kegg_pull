import pytest as pt

import src.kegg_pull.kegg_url as ku
import src.kegg_pull.make_urls_from_entry_id_list as mu
import tests.utils as u


def test_validate(caplog, mocker):
    mock_entry_id_list = []

    mock_get_entry_id_list_from_kegg_list_api_operation = mocker.patch(
        'src.kegg_pull.make_urls_from_entry_id_list._get_entry_id_list_from_kegg_list_api_operation',
        return_value=mock_entry_id_list
    )

    mock_get_entry_id_list_from_file = mocker.patch(
        'src.kegg_pull.make_urls_from_entry_id_list._get_entry_id_list_from_file'
    )

    mock_make_urls_from_entry_id_list = mocker.patch(
        'src.kegg_pull.make_urls_from_entry_id_list._make_urls_from_entry_id_list'
    )

    database_type = 'vg'
    mu.make_urls_from_entry_id_list(database_type=database_type, entry_id_list_path='')
    mock_get_entry_id_list_from_kegg_list_api_operation.assert_called_once_with(database_type=database_type)
    mock_get_entry_id_list_from_file.assert_not_called()

    mock_make_urls_from_entry_id_list.assert_called_once_with(
        entry_id_list=mock_entry_id_list, n_entries_per_url=mu.MAX_KEGG_ENTRY_IDS_PER_GET_URL, entry_field=None
    )

    u.assert_warning(
        file_name='make_urls_from_entry_id_list.py', func_name='_validate',
        message='Both a database type and file path to an entry ID list are specified. Ignoring the entry ID list '
                'path... ', caplog=caplog
    )

    with pt.raises(ValueError) as e:
        mu.make_urls_from_entry_id_list()

    u.assert_expected_error_message(
        expected_message='Required: Either a file containing a list of KEGG entry IDs or the name of a KEGG database '
                         'from which the entry IDs can be pulled. Neither are provided', e=e
    )


# TODO: Test with and without entry field
# TODO: Test with entry field that can pull multiple and entry field that only pulls single
# TODO: Test getting from file (mock open)
def test_make_urls_from_entry_id_list(mocker):
    expected_urls = [
        f'{ku.BASE_URL}/get/cpd:C22501+cpd:C22502+cpd:C22500+cpd:C22504+cpd:C22506+cpd:C22507+cpd:C22509+cpd:C22510+cpd:C22511+cpd:C22512',
        f'{ku.BASE_URL}/get/cpd:C22513+cpd:C22514'
    ]

    database_type = 'compound'

    mock_single_pull = _get_mock_single_pull(
        mocker=mocker, expected_url=f'{ku.BASE_URL}/list/{database_type}'
    )

    get_urls: list = mu.make_urls_from_entry_id_list(database_type=database_type)
    mock_single_pull.assert_called_once()

    for get_kegg_url, expected_url in zip(get_urls, expected_urls):
        assert get_kegg_url.url == expected_url


def _get_mock_single_pull(mocker, expected_url: str):
    mock_response_body = '''
    cpd:C22501	alpha-D-Xylulofuranose
    cpd:C22502	alpha-D-Fructofuranose; alpha-D-Fructose
    cpd:C22500	2,8-Dihydroxyadenine
    cpd:C22504	cis-Alkene
    cpd:C22506	Archaeal dolichyl alpha-D-glucosyl phosphate; Dolichyl alpha-D-glucosyl phosphate
    cpd:C22507	6-Sulfo-D-rhamnose
    cpd:C22509	3',5'-Cyclic UMP; Uridine 3',5'-cyclic monophosphate; cUMP
    cpd:C22510	4-Deoxy-4-sulfo-D-erythrose
    cpd:C22511	4-Deoxy-4-sulfo-D-erythrulose
    cpd:C22512	Solabiose
    cpd:C22513	sn-3-O-(Farnesylgeranyl)glycerol 1-phosphate
    cpd:C22514	2,3-Bis-O-(geranylfarnesyl)-sn-glycerol 1-phosphate
    '''

    mock_response = mocker.MagicMock(text=mock_response_body)

    def mock_single_pull(kegg_url: ku.AbstractKEGGurl):
        assert kegg_url.url == expected_url

        return mock_response

    mock_single_pull = mocker.patch(
        f'src.kegg_pull.make_urls_from_entry_id_list.sp.single_pull',
        wraps=mock_single_pull
    )

    return mock_single_pull
