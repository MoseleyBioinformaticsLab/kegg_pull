import pytest as pt

import kegg_pull.entry_ids_cli as ei_cli
import dev.utils as u

entry_ids_mock = ['a', 'b']
expected_output: str = '\n'.join(entry_ids_mock)


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=ei_cli, subcommand='entry-ids')


test_main_data = [
    (['entry-ids', 'database', 'compound'], 'entry_ids_cli.ei.from_database', {'database_name': 'compound'}, None),
    (
        ['entry-ids', 'keywords', 'pathway', 'k1,,k2'], 'entry_ids_cli.ei.from_keywords',
        {'database_name': 'pathway', 'keywords': ['k1', 'k2']}, None
    ),
    (
        ['entry-ids', 'molecular-attribute', 'drug', '--formula=CO2'], 'entry_ids_cli.ei.from_molecular_attribute',
        {'database_name': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None}, None
    ),
    (
        ['entry-ids', 'molecular-attribute', 'drug', '--em=20.2'], 'entry_ids_cli.ei.from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None}, None
    ),
    (
        ['entry-ids', 'molecular-attribute', 'drug', '--mw=202'], 'entry_ids_cli.ei.from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202}, None
    ),
    (
        ['entry-ids', 'molecular-attribute', 'drug', '--em=20.2', '--em=30.3'], 'entry_ids_cli.ei.from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': (20.2, 30.3), 'molecular_weight': None}, None
    ),
    (
        ['entry-ids', 'molecular-attribute', 'drug', '--mw=202', '--mw=303'],
        'entry_ids_cli.ei.from_molecular_attribute',
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202, 303)}, None
    ),
    (
        ['entry-ids', 'keywords', 'pathway', '-'], 'entry_ids_cli.ei.from_keywords',
        {'database_name': 'pathway', 'keywords': ['k1', 'k2']}, 'k1\nk2'
    )
]
@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_main_data)
def test_main_print(mocker, args: list, method: str, kwargs: dict, stdin_mock: str):
    u.test_main_print(
        mocker=mocker, argv_mock=args, stdin_mock=stdin_mock, method=method, method_return_value=entry_ids_mock,
        method_kwargs=kwargs, module=ei_cli, expected_output=expected_output
    )


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_main_data)
def test_main_file(mocker, args: list, method: str, kwargs: dict, output_file: str, stdin_mock: str):
    u.test_main_file(
        mocker=mocker, argv_mock=args, output_file=output_file, stdin_mock=stdin_mock, method=method,
        method_return_value=entry_ids_mock, method_kwargs=kwargs, module=ei_cli, expected_output=expected_output
    )


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_main_data)
def test_main_zip_archive(mocker, args: list, method: str, kwargs: dict, zip_archive_data: tuple, stdin_mock: str):
    u.test_main_zip_archive(
        mocker=mocker, argv_mock=args, zip_archive_data=zip_archive_data, stdin_mock=stdin_mock, method=method,
        method_return_value=entry_ids_mock, method_kwargs=kwargs, module=ei_cli, expected_output=expected_output
    )
