from pytest import raises

from src.kegg_pull.kegg_get_url_generator import KEGGgetURLgenerator
from tests.utils import assert_expected_error_message, assert_warning


def test_validate(caplog):
    KEGGgetURLgenerator(database_type='', entry_id_list_path='')

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
