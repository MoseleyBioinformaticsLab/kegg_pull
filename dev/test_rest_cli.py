import pytest as pt
import unittest.mock as mock
import os
import typing as t
import zipfile as zf

import kegg_pull.rest as r
import kegg_pull.rest_cli as r_cli
import kegg_pull.kegg_url as ku
import dev.utils as u


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


test_main_args = [
    ['info', 'ligand'], ['list', 'module'], ['get', 'x,y,z'], ['get', 'a', '--entry-field=image'],
    ['find', 'pathway', 'a,b,c'], ['find', 'drug', '--formula=CO2'], ['find', 'drug', '--exact-mass=20.2'],
    ['find', 'drug', '--molecular-weight=202'], ['find', 'drug', '--exact-mass=20.2', '--exact-mass=30.3'],
    ['find', 'drug', '--molecular-weight=202', '--molecular-weight=303'], ['conv', 'kegg-db', 'out-db'],
    ['conv', '--conv-target=genes', 'eid1,eid2'], ['link', 'target-db', 'source-db'],
    ['link', '--link-target=target-db', 'x,y'], ['ddi', 'de1,de2,de3']
]

test_main_kwargs = [
    {'database_name': 'ligand'}, {'database_name': 'module'}, {'entry_ids': ['x', 'y', 'z'], 'entry_field': None},
    {'entry_ids': ['a'], 'entry_field': 'image'}, {'database_name': 'pathway', 'keywords': ['a', 'b', 'c']},
    {'database_name': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None},
    {'database_name': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None},
    {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202},
    {'database_name': 'drug', 'formula': None, 'exact_mass': (20.2,30.3), 'molecular_weight': None},
    {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202,303)},
    {'kegg_database_name': 'kegg-db', 'outside_database_name': 'out-db'},
    {'target_database_name': 'genes', 'entry_ids': ['eid1', 'eid2']},
    {'target_database_name': 'target-db', 'source_database_name': 'source-db'},
    {'target_database_name': 'target-db', 'entry_ids': ['x', 'y']}, {'drug_entry_ids': ['de1', 'de2', 'de3']}
]


test_main_data = [
    ('info', test_main_args[0], test_main_kwargs[0], False),
    ('list', test_main_args[1], test_main_kwargs[1], False),
    ('get', test_main_args[2], test_main_kwargs[2], False),
    ('get', test_main_args[3], test_main_kwargs[3], True),
    ('keywords_find', test_main_args[4], test_main_kwargs[4], False),
    ('molecular_find', test_main_args[5], test_main_kwargs[5], False),
    ('molecular_find', test_main_args[6], test_main_kwargs[6], False),
    ('molecular_find', test_main_args[7], test_main_kwargs[7], False),
    ('molecular_find', test_main_args[8], test_main_kwargs[8], False),
    ('molecular_find', test_main_args[9], test_main_kwargs[9], False),
    ('database_conv', test_main_args[10], test_main_kwargs[10], False),
    ('entries_conv', test_main_args[11], test_main_kwargs[11], False),
    ('database_link', test_main_args[12], test_main_kwargs[12], False),
    ('entries_link', test_main_args[13], test_main_kwargs[13], False),
    ('ddi', test_main_args[14], test_main_kwargs[14], False)
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
    args: list = args.copy()
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

@pt.fixture(name='test_result', params=[True, False])
def get_test_result(request):
    yield request.param


test_main_test_data = [
    (ku.InfoKEGGurl, test_main_args[0], test_main_kwargs[0]),
    (ku.ListKEGGurl, test_main_args[1], test_main_kwargs[1]),
    (ku.GetKEGGurl, test_main_args[2], test_main_kwargs[2]),
    (ku.GetKEGGurl, test_main_args[3], test_main_kwargs[3]),
    (ku.KeywordsFindKEGGurl, test_main_args[4], test_main_kwargs[4]),
    (ku.MolecularFindKEGGurl, test_main_args[5], test_main_kwargs[5]),
    (ku.MolecularFindKEGGurl, test_main_args[6], test_main_kwargs[6]),
    (ku.MolecularFindKEGGurl, test_main_args[7], test_main_kwargs[7]),
    (ku.MolecularFindKEGGurl, test_main_args[8], test_main_kwargs[8]),
    (ku.MolecularFindKEGGurl, test_main_args[9], test_main_kwargs[9]),
    (ku.DatabaseConvKEGGurl, test_main_args[10], test_main_kwargs[10]),
    (ku.EntriesConvKEGGurl, test_main_args[11], test_main_kwargs[11]),
    (ku.DatabaseLinkKEGGurl, test_main_args[12], test_main_kwargs[12]),
    (ku.EntriesLinkKEGGurl, test_main_args[13], test_main_kwargs[13]),
    (ku.DdiKEGGurl, test_main_args[14], test_main_kwargs[14])
]
@pt.mark.parametrize('KEGGurl,args,kwargs', test_main_test_data)
def test_main_test(mocker, KEGGurl: t.Type, args: list, kwargs: dict, test_result: bool):
    test_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest_cli.r.KEGGrest.test', return_value=test_result)
    argv_mock = ['kegg_pull', 'rest']
    argv_mock.extend(args)
    argv_mock.append('--test')
    mocker.patch('sys.argv', argv_mock)
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    r_cli.main()
    test_mock.assert_called_with(KEGGurl=KEGGurl, **kwargs)
    print_mock.assert_called_once_with(test_result)


@pt.fixture(name='zip_archive_data', params=['kegg-response.txt', None])
def remove_zip_archive(request):
    zip_file_name: str = request.param
    zip_archive_path = 'kegg-response.zip'

    yield zip_archive_path, zip_file_name

    os.remove(zip_archive_path)


@pt.mark.parametrize('rest_method,args,kwargs,is_binary', test_main_data)
def test_main_zip_archive(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, zip_archive_data: tuple):
    zip_archive_path, zip_file_name = zip_archive_data
    args: list = args.copy()
    args.append(f'--output={zip_archive_path}')

    if zip_file_name is not None:
        args.append(f'--zip-file={zip_file_name}')

    kegg_response: mocker.MagicMock = _test_main(mocker=mocker, rest_method=rest_method, args=args, kwargs=kwargs)

    if zip_file_name is None:
        zip_file_name = 'kegg-response'

    with zf.ZipFile(zip_archive_path, 'r') as zip_file:
        actual_file_contents: bytes = zip_file.read(zip_file_name)

        if not is_binary:
            actual_file_contents: str = actual_file_contents.decode()
            expected_file_contents: str = kegg_response.text_body
        else:
            expected_file_contents: bytes = kegg_response.binary_body

    assert actual_file_contents == expected_file_contents
