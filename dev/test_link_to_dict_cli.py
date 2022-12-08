import pytest as pt

import kegg_pull.link_to_dict_cli as ltd_cli
import dev.utils as u

mapping_mock = {'k1': {'v1'}, 'k2': {'v1', 'v2'}, 'k3': {'v3', 'v4'}}
expected_output = '{\n  "k1": [\n    "v1"\n  ],\n  "k2": [\n    "v1",\n    "v2"\n  ],\n  "k3": [\n    "v3",\n    "v4"\n  ]\n}'


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=ltd_cli, subcommand='link-to-dict')


test_main_data = [
    (
        ['link-to-dict', 'compound', 'pathway'], 'link_to_dict_cli.ltd.database_link',
        {'target_database_name': 'compound', 'source_database_name': 'pathway'}, None
    ),
    (
        ['link-to-dict', '--link-target=glycan', 'e1,e2,e3'], 'link_to_dict_cli.ltd.entries_link',
        {'target_database_name': 'glycan', 'entry_ids': ['e1', 'e2', 'e3']}, None
    ),
    (
        ['link-to-dict', '--link-target=ko', '-'], 'link_to_dict_cli.ltd.entries_link',
        {'target_database_name': 'ko', 'entry_ids': ['e1', 'e2', 'e3']}, ' e1\ne2\t\ne3\n\n'
    ),
    (
        ['link-to-dict', 'pathway-to-compound', '--add-glycans', '--add-drugs'], 'link_to_dict_cli.ltd.pathway_to_compound',
        {'add_glycans': True, 'add_drugs': True}, None
    ),
    (
        ['link-to-dict', 'reaction-to-compound', '--add-glycans', '--add-drugs'], 'link_to_dict_cli.ltd.reaction_to_compound',
        {'add_glycans': True, 'add_drugs': True}, None
    ),
    (
        ['link-to-dict', 'gene-to-compound', '--add-glycans', '--add-drugs'], 'link_to_dict_cli.ltd.gene_to_compound',
        {'add_glycans': True, 'add_drugs': True}, None
    ),
    (
        ['link-to-dict', 'compound-to-pathway', '--add-glycans', '--add-drugs'], 'link_to_dict_cli.ltd.compound_to_pathway',
        {'add_glycans': True, 'add_drugs': True}, None
    ),
    (
        ['link-to-dict', 'compound-to-reaction', '--add-glycans', '--add-drugs'], 'link_to_dict_cli.ltd.compound_to_reaction',
        {'add_glycans': True, 'add_drugs': True}, None
    ),
    (
        ['link-to-dict', 'compound-to-gene', '--add-glycans', '--add-drugs'], 'link_to_dict_cli.ltd.compound_to_gene',
        {'add_glycans': True, 'add_drugs': True}, None
    ),
    (
        ['link-to-dict', 'pathway-to-gene'], 'link_to_dict_cli.ltd.pathway_to_gene', {}, None
    ),
    (
        ['link-to-dict', 'pathway-to-reaction'], 'link_to_dict_cli.ltd.pathway_to_reaction', {}, None
    ),
    (
        ['link-to-dict', 'gene-to-pathway'], 'link_to_dict_cli.ltd.gene_to_pathway', {}, None
    ),
    (
        ['link-to-dict', 'reaction-to-pathway'], 'link_to_dict_cli.ltd.reaction_to_pathway', {}, None
    ),
    (
        ['link-to-dict', 'reaction-to-gene'], 'link_to_dict_cli.ltd.reaction_to_gene', {}, None
    ),
    (
        ['link-to-dict', 'gene-to-reaction'], 'link_to_dict_cli.ltd.gene_to_reaction', {}, None
    )
]
# noinspection DuplicatedCode
@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_main_data)
def test_main_print(mocker, args: list, method: str, kwargs: dict, stdin_mock: str):
    u.test_main_print(
        mocker=mocker, argv_mock=args, stdin_mock=stdin_mock, method=method, method_return_value=mapping_mock, method_kwargs=kwargs,
        module=ltd_cli, expected_output=expected_output
    )


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_main_data)
def test_main_file(mocker, args: list, method: str, kwargs: dict, stdin_mock: str, output_file: str):
    u.test_main_file(
        mocker=mocker, argv_mock=args, output_file=output_file, stdin_mock=stdin_mock, method=method,
        method_return_value=mapping_mock, method_kwargs=kwargs, module=ltd_cli, expected_output=expected_output
    )


@pt.mark.parametrize('args,method,kwargs,stdin_mock', test_main_data)
def test_main_zip_archive(mocker, args: list, method: str, kwargs: dict, stdin_mock: str, zip_archive_data: tuple):
    u.test_main_zip_archive(
        mocker=mocker, argv_mock=args, zip_archive_data=zip_archive_data, stdin_mock=stdin_mock, method=method,
        method_return_value=mapping_mock, method_kwargs=kwargs, module=ltd_cli, expected_output=expected_output
    )
