import pytest as pt
import os

import kegg_pull.entry_ids_cli as ei_cli
import tests.utils as u


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=ei_cli, subcommand='entry-ids')


test_main_data = [
    (['from-database', 'compound'], 'from_database', {'database_name': 'compound'}),
    (['from-file', 'file.txt'], 'from_file', {'file_path': 'file.txt'}),
    (['from-keywords', 'pathway', 'k1,k2'], 'from_keywords', {'database_name': 'pathway', 'keywords': ['k1', 'k2']}),
    (
        ['from-molecular-attribute', 'drug', '--formula=CO2'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None}
    ),
    (
        ['from-molecular-attribute', 'drug', '--exact-mass=20.2'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None}
    ),
    (
        ['from-molecular-attribute', 'drug', '--molecular-weight=202'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202}
    ),
    (
        ['from-molecular-attribute', 'drug', '--exact-mass=20.2', '--exact-mass=30.3'], 'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': (20.2, 30.3), 'molecular_weight': None}
    ),
    (
        ['from-molecular-attribute', 'drug', '--molecular-weight=202', '--molecular-weight=303'],
        'from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202, 303)}
    )
]
@pt.mark.parametrize('args,method,kwargs', test_main_data)
def test_main_print(mocker, args: list, method: str, kwargs: dict):
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    entry_ids_mock: list = _test_main(mocker=mocker, args=args, method=method, kwargs=kwargs)
    for actual_printed_id, expected_printed_id in zip(print_mock.call_args_list, entry_ids_mock):
        (actual_printed_id,) = actual_printed_id.args

        assert actual_printed_id == expected_printed_id


def _test_main(mocker, args: list, method: str, kwargs: dict) -> list:
    argv_mock = ['kegg_pull', 'entry-ids']
    argv_mock.extend(args)
    mocker.patch('sys.argv', argv_mock)
    entry_ids_mock = ['a', 'b']

    get_entry_ids_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.entry_ids.EntryIdsGetter.{method}', return_value=entry_ids_mock
    )

    ei_cli.main()
    get_entry_ids_mock.assert_called_once_with(**kwargs)

    return entry_ids_mock


@pt.fixture(name='output_file')
def output_file_mock():
    output_file = 'output-file-mock.txt'

    yield output_file

    os.remove(output_file)


@pt.mark.parametrize('args,method,kwargs', test_main_data)
def test_main_file(mocker, args: list, method: str, kwargs: dict, output_file: str):
    args.append(f'--output={output_file}')
    entry_ids_mock: list = _test_main(mocker=mocker, args=args, method=method, kwargs=kwargs)
    expected_output = '\n'.join(entry_ids_mock) + '\n'

    with open(output_file, 'r') as file:
        actual_output: str = file.read()

    assert actual_output == expected_output
