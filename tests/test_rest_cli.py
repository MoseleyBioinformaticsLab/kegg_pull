import pytest as pt
import unittest.mock as mock
import os
import typing as t

import kegg_pull.rest as r
import kegg_pull.rest_cli as r_cli
import tests.utils as u


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=r_cli, subcommand='rest')


test_main_exception_data = [
    ('The request to the KEGG web API failed with the following URL: url/mock', r.KEGGresponse.Status.FAILED),
    ('The request to the KEGG web API timed out with the following URL: url/mock', r.KEGGresponse.Status.TIMEOUT)
]
@pt.mark.parametrize('expected_message,status', test_main_exception_data)
def test_main_exception(mocker, expected_message: str, status):
    mocker.patch(
        'kegg_pull.rest.KEGGrest.info',
        return_value=mocker.MagicMock(status=status, kegg_url=mocker.MagicMock(url='url/mock'))
    )

    mocker.patch('sys.argv', ['kegg_pull', 'rest', 'info', 'db-name'])

    with pt.raises(RuntimeError) as error:
        r_cli.main()

    u.assert_expected_error_message(expected_message=expected_message, error=error)


test_main_data = [
    ('info', ['info', 'ligand'], {'database_name': 'ligand'}, False),
    ('list', ['list', 'module'], {'database_name': 'module'}, False),
    ('get', ['get', 'x,y,z'], {'entry_ids': ['x', 'y', 'z'], 'entry_field': None}, False),
    ('get', ['get', 'a', '--entry-field=image'], {'entry_ids': ['a'], 'entry_field': 'image'}, True),
    ('keywords_find', ['find', 'pathway', 'a,b,c'], {'database_name': 'pathway', 'keywords': ['a', 'b', 'c']}, False),
    (
        'molecular_find', ['find', 'drug', '--formula=CO2'],
        {'database_name': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None}, False
    ),
    (
        'molecular_find', ['find', 'drug', '--exact-mass=20.2'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None}, False
    ),
    (
        'molecular_find', ['find', 'drug', '--molecular-weight=202'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202}, False
    ),    (
        'molecular_find', ['find', 'drug', '--exact-mass=20.2', '--exact-mass=30.3'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': (20.2,30.3), 'molecular_weight': None}, False
    ),
    (
        'molecular_find', ['find', 'drug', '--molecular-weight=202', '--molecular-weight=303'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202,303)}, False
    ),
    (
        'database_conv', ['conv', 'kegg-db', 'out-db'],
        {'kegg_database_name': 'kegg-db', 'outside_database_name': 'out-db'}, False
    ),
    (
        'entries_conv', ['conv', '--conv-target=genes', 'eid1,eid2'],
        {'target_database_name': 'genes', 'entry_ids': ['eid1', 'eid2']}, False
    ),
    (
        'database_link', ['link', 'target-db', 'source-db'],
        {'target_database_name': 'target-db', 'source_database_name': 'source-db'}, False
    ),
    (
        'entries_link', ['link', '--link-target=target-db', 'x,y'],
        {'target_database_name': 'target-db', 'entry_ids': ['x', 'y']}, False
    ),
    ('ddi', ['ddi', 'de1,de2,de3'], {'drug_entry_ids': ['de1', 'de2', 'de3']}, False)
]
@pt.mark.parametrize('rest_method,args,kwargs,is_binary', test_main_data)
def test_main_print(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, caplog):
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    kegg_response_mock: mocker.MagicMock = _test_main(mocker=mocker, rest_method=rest_method, args=args, kwargs=kwargs)

    if is_binary:
        u.assert_warning(message='Printing binary response body', caplog=caplog)
        print_mock.assert_called_once_with(kegg_response_mock.binary_body)
    else:
        print_mock.assert_called_once_with(kegg_response_mock.text_body)


def _test_main(mocker, rest_method: str, args: list, kwargs: dict) -> mock.MagicMock:
    argv_mock = ['kegg_pull', 'rest']
    argv_mock.extend(args)
    mocker.patch('sys.argv', argv_mock)

    kegg_response_mock = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body='text body mock', binary_body=b'binary body mock'
    )

    rest_method_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.rest.KEGGrest.{rest_method}', return_value=kegg_response_mock
    )

    r_cli.main()
    rest_method_mock.assert_called_once_with(**kwargs)

    return kegg_response_mock


@pt.fixture(name='output_file')
def output_file_mock():
    output_file = 'output.txt'

    yield output_file

    os.remove(output_file)


@pt.mark.parametrize('rest_method,args,kwargs,is_binary', test_main_data)
def test_main_file(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, output_file: str):
    args.append(f'--output={output_file}')
    kegg_response: mocker.MagicMock = _test_main(mocker=mocker, rest_method=rest_method, args=args, kwargs=kwargs)

    if is_binary:
        read_type = 'rb'
        expected_file_contents: bytes = kegg_response.binary_body
    else:
        read_type = 'r'
        expected_file_contents: str = kegg_response.text_body

    with open(output_file, read_type) as file:
        actual_file_contents: t.Union[str, bytes] = file.read()

        assert actual_file_contents == expected_file_contents


