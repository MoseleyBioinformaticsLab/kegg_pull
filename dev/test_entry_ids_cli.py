import pytest as pt
import os
import shutil as sh
import zipfile as zf

import kegg_pull.entry_ids_cli as ei_cli
import dev.utils as u


def test_help(mocker):
    u.assert_cli_help(mocker=mocker, module=ei_cli, subcommand='entry-ids')

test_data = [
    (['database', 'compound'], 'from_database', {'database': 'compound'}, None),
    (['keywords', 'pathway', 'k1,,k2'], 'from_keywords', {'database': 'pathway', 'keywords': ['k1', 'k2']}, None),
    (
        ['molec-attr', 'drug', '--formula=CO2'], 'from_molecular_attribute',
        {'database': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None}, None
    ),
    (
        ['molec-attr', 'drug', '--em=20.2'], 'from_molecular_attribute',
        {'database': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None}, None
    ),
    (
        ['molec-attr', 'drug', '--mw=202'], 'from_molecular_attribute',
        {'database': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202}, None
    ),
    (
        ['molec-attr', 'drug', '--em=20.2', '--em=30.3'], 'from_molecular_attribute',
        {'database': 'drug', 'formula': None, 'exact_mass': (20.2, 30.3), 'molecular_weight': None}, None
    ),
    (
        ['molec-attr', 'drug', '--mw=202', '--mw=303'],
        'from_molecular_attribute',
        {'database': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202, 303)}, None
    ),
    (['keywords', 'pathway', '-'], 'from_keywords', {'database': 'pathway', 'keywords': ['k1', 'k2']}, 'k1\nk2')
]
@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_data)
def test_print(mocker, args: list, method: str, kwargs: dict, stdin_mock: str):
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    entry_ids_mock: list = _test_cli(mocker=mocker, args=args, method=method, kwargs=kwargs, stdin_mock=stdin_mock)
    print_mock.assert_called_once_with('\n'.join(entry_ids_mock))


def _test_cli(mocker, args: list, method: str, kwargs: dict, stdin_mock: str) -> list:
    argv_mock = ['kegg_pull', 'entry-ids']
    argv_mock.extend(args)
    mocker.patch('sys.argv', argv_mock)
    entry_ids_mock = ['a', 'b']
    stdin_mock: mocker.MagicMock = mocker.patch('kegg_pull._utils.sys.stdin.read', return_value=stdin_mock) if stdin_mock else None

    get_entry_ids_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.entry_ids_cli.ei.{method}', return_value=entry_ids_mock
    )

    ei_cli.main()
    get_entry_ids_mock.assert_called_once_with(**kwargs)

    if stdin_mock:
        stdin_mock.assert_called_once_with()

    return entry_ids_mock


@pt.fixture(name='output_file', params=['dir/subdir/file.txt', 'dir/file.txt', './file.txt', 'file.txt'])
def output_file_mock(request):
    output_file: str = request.param

    yield output_file

    os.remove(output_file)
    sh.rmtree('dir', ignore_errors=True)


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_data)
def test_file(mocker, args: list, method: str, kwargs: dict, output_file: str, stdin_mock: str):
    args: list = args.copy()
    args.append(f'--output={output_file}')
    entry_ids_mock: list = _test_cli(mocker=mocker, args=args, method=method, kwargs=kwargs, stdin_mock=stdin_mock)
    expected_output = '\n'.join(entry_ids_mock)

    with open(output_file, 'r') as file:
        actual_output: str = file.read()

    assert actual_output == expected_output


@pt.fixture(name='zip_archive_data', params=['entry-ids.txt', 'directory/entry-ids.txt', '/entry-ids.txt', '/directory/entry-ids.txt'])
def remove_zip_archive(request):
    zip_file_name: str = request.param
    zip_archive_path = 'entry-ids.zip'

    yield zip_archive_path, zip_file_name

    os.remove(zip_archive_path)

@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_data)
def test_zip_archive(mocker, args: list, method: str, kwargs: dict, zip_archive_data: tuple, stdin_mock: str):
    zip_archive_path, zip_file_name = zip_archive_data
    args: list = args.copy()
    args.append(f'--output={zip_archive_path}:{zip_file_name}')
    entry_ids_mock: list = _test_cli(mocker=mocker, args=args, method=method, kwargs=kwargs, stdin_mock=stdin_mock)
    expected_output = '\n'.join(entry_ids_mock)

    with zf.ZipFile(zip_archive_path, 'r') as zip_file:
        actual_output: str = zip_file.read(zip_file_name).decode()

    assert actual_output == expected_output
