# noinspection PyPackageRequirements
import pytest as pt
import typing as t
import kegg_pull.map_cli as map_cli
import dev.utils as u

mapping_mock = {'k1': {'v1'}, 'k2': {'v1', 'v2'}, 'k3': {'v3', 'v4'}}


def test_help(mocker):
    u.assert_help(mocker=mocker, module=map_cli, subcommand='map')


test_data = [
    (['enzyme', 'compound'], 'database_map',
     {'source_database': 'enzyme', 'target_database': 'compound', 'deduplicate': False, 'add_glycans': False,
      'add_drugs': False}, None),
    (['compound', 'reaction', '--add-glycans', '--add-drugs'], 'database_map',
     {'source_database': 'compound', 'target_database': 'reaction', 'deduplicate': False, 'add_glycans': True,
      'add_drugs': True}, None),
    (['pathway', 'reaction', '--deduplicate'], 'database_map',
     {'source_database': 'pathway', 'target_database': 'reaction', 'deduplicate': True, 'add_glycans': False,
      'add_drugs': False}, None),
    (['entry-ids', 'e1,e2,e3', 'glycan'], 'entries_map',
     {'entry_ids': ['e1', 'e2', 'e3'], 'target_database': 'glycan', 'reverse': False}, None),
    (['entry-ids', '-', 'ko', '--reverse'], 'entries_map',
     {'entry_ids': ['e1', 'e2', 'e3'], 'target_database': 'ko', 'reverse': True}, ' e1\ne2\t\ne3\n\n'),
    (['ko', 'reaction', 'compound'], 'indirect',
     {'source_database': 'ko', 'intermediate_database': 'reaction', 'target_database': 'compound',
      'deduplicate': False, 'add_glycans': False, 'add_drugs': False}, None),
    (['pathway', 'reaction', 'ko', '--deduplicate'], 'indirect',
     {'source_database': 'pathway', 'intermediate_database': 'reaction', 'target_database': 'ko',
      'deduplicate': True, 'add_glycans': False, 'add_drugs': False}, None),
    (['compound', 'reaction', 'ko', '--add-glycans', '--add-drugs'], 'indirect',
     {'source_database': 'compound', 'intermediate_database': 'reaction', 'target_database': 'ko',
      'deduplicate': False, 'add_glycans': True, 'add_drugs': True}, None)]


def _prepare_input(args: list, method: str) -> t.Tuple[list, str, str]:
    args = ['map'] + args
    method = f'map_cli.kmap.{method}'
    expected_output = '{\n  "k1": [\n    "v1"\n  ],\n  "k2": [\n    "v1",\n    "v2"\n  ],\n  "k3": [\n    "v3",\n    "v4"\n  ]\n}'
    return args, method, expected_output


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_data)
def test_print(mocker, args: list, method: str, kwargs: dict, stdin_mock: str):
    args, method, expected_output = _prepare_input(args=args, method=method)
    u.test_print(
        mocker=mocker, argv_mock=args, stdin_mock=stdin_mock, method=method, method_return_value=mapping_mock, method_kwargs=kwargs,
        module=map_cli, expected_output=expected_output)


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_data)
def test_file(mocker, args: list, method: str, kwargs: dict, stdin_mock: str, output_file: str):
    args, method, expected_output = _prepare_input(args=args, method=method)
    u.test_file(
        mocker=mocker, argv_mock=args, output_file=output_file, stdin_mock=stdin_mock, method=method,
        method_return_value=mapping_mock, method_kwargs=kwargs, module=map_cli, expected_output=expected_output)


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_data)
def test_zip_archive(mocker, args: list, method: str, kwargs: dict, stdin_mock: str, zip_archive_data: tuple):
    args, method, expected_output = _prepare_input(args=args, method=method)
    u.test_zip_archive(
        mocker=mocker, argv_mock=args, zip_archive_data=zip_archive_data, stdin_mock=stdin_mock, method=method,
        method_return_value=mapping_mock, method_kwargs=kwargs, module=map_cli, expected_output=expected_output)
