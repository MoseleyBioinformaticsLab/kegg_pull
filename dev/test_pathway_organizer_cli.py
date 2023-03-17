# noinspection PyPackageRequirements
import pytest as pt
import json
import kegg_pull.pathway_organizer as po
import kegg_pull.pathway_organizer_cli as po_cli
import dev.utils as u


def test_help(mocker):
    u.assert_help(mocker=mocker, module=po_cli, subcommand='pathway-organizer')


method = 'pathway_organizer_cli.po.PathwayOrganizer.load_from_kegg'
test_data = [
    (['pathway-organizer', '--tln=-', '--fn=-'], {'top_level_nodes': {'node1'}, 'filter_nodes': {'node2', 'node3'}},
     ' node1\n---\nnode2\t\nnode3 '),
    (['pathway-organizer', '--tln=-', '--fn=node2,node3,node4'],
     {'top_level_nodes': {'node1', 'node5'}, 'filter_nodes': {'node2', 'node3', 'node4'}}, '\nnode1\n node5\n'),
    (['pathway-organizer', '--tln=node1', '--fn=-'], {'top_level_nodes': {'node1'}, 'filter_nodes': {'node2'}}, 'node2'),
    (['pathway-organizer', '--tln=node1,node2', '--fn=node3'], {'top_level_nodes': {'node1', 'node2'}, 'filter_nodes': {'node3'}}, None),
    (['pathway-organizer', '--tln=-'], {'top_level_nodes': {'node1', 'node2', 'node3'}, 'filter_nodes': None}, 'node1\nnode2\nnode3'),
    (['pathway-organizer', '--fn=-'], {'top_level_nodes': None, 'filter_nodes': {'node1', 'node2', 'node3'}}, 'node1\nnode2\nnode3'),
    (['pathway-organizer', '--tln=node1,node2,node3'], {'top_level_nodes': {'node1', 'node2', 'node3'}, 'filter_nodes': None}, None),
    (['pathway-organizer', '--fn=node1,node2,node3'], {'top_level_nodes': None, 'filter_nodes': {'node1', 'node2', 'node3'}}, None),
    (['pathway-organizer'], {'top_level_nodes': None, 'filter_nodes': None}, None)]


@pt.mark.parametrize('args,kwargs,stdin_mock', test_data)
def test_print(mocker, args: list, kwargs: dict, stdin_mock: str):
    pathway_org_mock, expected_output = _get_mock_pathway_org_and_expected_output(mocker=mocker)
    u.test_print(
        mocker=mocker, argv_mock=args, stdin_mock=stdin_mock, method=method, method_return_value=pathway_org_mock, method_kwargs=kwargs,
        module=po_cli, expected_output=expected_output)


def _get_mock_pathway_org_and_expected_output(mocker):
    u.mock_non_instantiable(mocker=mocker)
    hierarchy_nodes_mock: po.HierarchyNodes = {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': ['a'], 'entry_id': 'd'}}
    pathway_org_mock = po.PathwayOrganizer()
    pathway_org_mock.hierarchy_nodes = hierarchy_nodes_mock
    expected_output: str = json.dumps(hierarchy_nodes_mock, indent=2)
    return pathway_org_mock, expected_output


@pt.mark.parametrize('args,kwargs,stdin_mock', test_data)
def test_file(mocker, args: list, kwargs: dict, stdin_mock: str, output_file: str):
    pathway_org_mock, expected_output = _get_mock_pathway_org_and_expected_output(mocker=mocker)
    u.test_file(
        mocker=mocker, argv_mock=args, output_file=output_file, stdin_mock=stdin_mock, method=method,
        method_return_value=pathway_org_mock, method_kwargs=kwargs, module=po_cli, expected_output=expected_output)


@pt.mark.parametrize('args,kwargs,stdin_mock', test_data)
def test_zip_archive(mocker, args: list, kwargs: dict, stdin_mock: str, zip_archive_data: tuple):
    pathway_org_mock, expected_output = _get_mock_pathway_org_and_expected_output(mocker=mocker)
    u.test_zip_archive(
        mocker=mocker, argv_mock=args, zip_archive_data=zip_archive_data, stdin_mock=stdin_mock, method=method,
        method_return_value=pathway_org_mock, method_kwargs=kwargs, module=po_cli, expected_output=expected_output)
