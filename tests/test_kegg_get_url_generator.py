from pytest import raises

from src.kegg_pull.kegg_url import BASE_URL
from src.kegg_pull.kegg_get_url_generator import KEGGgetURLgenerator
from tests.utils import assert_expected_error_message, assert_warning


def test_validate(caplog, mocker):
    mock_get_entry_id_list_from_kegg_list_api_operation = mocker.patch(
        'src.kegg_pull.kegg_get_url_generator.KEGGgetURLgenerator._get_entry_id_list_from_kegg_list_api_operation'
    )

    mock_get_entry_id_list_from_file = mocker.patch(
        'src.kegg_pull.kegg_get_url_generator.KEGGgetURLgenerator._get_entry_id_list_from_file'
    )

    database_type = 'vg'
    KEGGgetURLgenerator(database_type=database_type, entry_id_list_path='')
    mock_get_entry_id_list_from_kegg_list_api_operation.assert_called_once_with(database_type=database_type)
    mock_get_entry_id_list_from_file.assert_not_called()

    assert_warning(
        file_name='kegg_get_url_generator.py', func_name='_validate',
        message='Both a database type and file path to an entry ID list are specified. Ignoring the entry ID list '
                'path... ', caplog=caplog
    )

    with raises(ValueError) as e:
        KEGGgetURLgenerator()

    assert_expected_error_message(
        expected_message='Required: Either a file containing a list of KEGG entry IDs or the name of a KEGG database '
                         'from which the entry IDs can be pulled. Neither are provided', e=e
    )


# TODO: Test with and without entry field
# TODO: Test with entry field that can pull multiple and entry field that only pulls single
# TODO: Test getting from file (mock open)
def test_iter(mocker):
    mock_response_body = '''
br:br08901	KEGG pathway maps
br:br08902	BRITE hierarchy files
br:br08904	BRITE table files
br:ko00001	KEGG Orthology (KO)
br:ko00002	KEGG modules
br:ko00003	KEGG reaction modules
br:br08907	KEGG networks
br:ko01000	Enzymes
br:ko01001	Protein kinases
br:ko01009	Protein phosphatases and associated proteins
br:ko01002	Peptidases and inhibitors
br:ko01003	Glycosyltransferases
    '''

    expected_urls = [
        f'{BASE_URL}/get/br:br08901+br:br08902+br:br08904+br:ko00001+br:ko00002+br:ko00003+br:br08907+br:ko01000+'
        'br:ko01001+br:ko01009',
        f'{BASE_URL}/get/br:ko01002+br:ko01003'
    ]

    mock_pull_single_from_kegg_return_value = mocker.MagicMock(text=mock_response_body)

    mock_pull_single_from_kegg = mocker.patch(
        'src.kegg_pull.kegg_get_url_generator.pull_single_from_kegg',
        return_value=mock_pull_single_from_kegg_return_value
    )

    kegg_get_url_generator = KEGGgetURLgenerator(database_type='brite')
    mock_pull_single_from_kegg.assert_called_once()

    for get_kegg_url, expected_url in zip(kegg_get_url_generator, expected_urls):
        assert get_kegg_url.url == expected_url
