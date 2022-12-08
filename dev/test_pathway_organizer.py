import pytest as pt
import json as j
import typing as t

import kegg_pull.pathway_organizer as po
import dev.utils as u


test_load_from_kegg_data = [
    (None, None, 'all-nodes.json'),
    ({'Metabolism', 'Genetic Information Processing'}, None, 'top-level-nodes.json'),
    (None, {'Genetic Information Processing', 'Global and overview maps', '00010  Glycolysis / Gluconeogenesis'}, 'filter-nodes.json')
]
@pt.mark.parametrize('top_level_nodes,filter_nodes,hierarchy_nodes_file', test_load_from_kegg_data)
def test_load_from_kegg(mocker, top_level_nodes: set, filter_nodes: set, hierarchy_nodes_file: str):
    def get_mock(**_) -> mocker.MagicMock:
        with open('dev/test_data/pathway-organizer/pathway-hierarchy.json', 'r') as file_:
            text_body_mock: str = file_.read()

        kegg_response_mock = mocker.MagicMock(text_body=text_body_mock)

        return kegg_response_mock

    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.pathway_organizer.r.KEGGrest.get', wraps=get_mock)
    pathway_organizer = po.PathwayOrganizer.load_from_kegg(top_level_nodes=top_level_nodes, filter_nodes=filter_nodes)
    get_mock.assert_called_once_with(entry_ids=['br:br08901'], entry_field='json')

    if top_level_nodes is not None:
        actual_top_level_nodes = {node_key for node_key, node_val in pathway_organizer.hierarchy_nodes.items() if node_val['level'] == 1}

        assert actual_top_level_nodes == top_level_nodes

    if filter_nodes is not None:
        for filter_node in filter_nodes:
            assert filter_node not in pathway_organizer.hierarchy_nodes.keys()

    expected_hierarchy_nodes: dict = _get_expected_hierarchy_nodes(hierarchy_nodes_file=hierarchy_nodes_file)

    assert pathway_organizer.hierarchy_nodes == expected_hierarchy_nodes


def _get_expected_hierarchy_nodes(hierarchy_nodes_file: str) -> dict:
    with open(f'dev/test_data/pathway-organizer/{hierarchy_nodes_file}') as file:
        expected_hierarchy_nodes: dict = j.load(file)

    return expected_hierarchy_nodes


def test_save_to_json(json_file_path: str):
    pathway_organizer = po.PathwayOrganizer()
    pathway_organizer.hierarchy_nodes = _get_expected_hierarchy_nodes(hierarchy_nodes_file='top-level-nodes.json')
    pathway_organizer.save_to_json(file_path=json_file_path)
    u.test_save_to_json(json_file_path=json_file_path, expected_saved_json_object=pathway_organizer.hierarchy_nodes)


def test_load_from_json(json_file_path: str):
    expected_hierarchy_nodes: dict = _get_expected_hierarchy_nodes(hierarchy_nodes_file='top-level-nodes.json')

    u.test_load_from_json(
        json_file_path=json_file_path, saved_object=expected_hierarchy_nodes, method=po.PathwayOrganizer.load_from_json,
        expected_loaded_object=expected_hierarchy_nodes, loaded_object_attribute='hierarchy_nodes'
    )


test_invalid_load_from_json_data = [
    1, 'a', [], [1, 2], ['a', 'b'], [[], []], [[1], [2]], [['a'], ['b']], [{}, {}], [{'a': {}, 'b': []}], {}, {'a': []}, {'a': {}},
    {'a': {'b': 1}}, {'a': {'name': 'b'}}, {'a': {'level': 1, 'b': 'c'}},
    {
        'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': None, 'entry-id': 'x'},
        '': {'name': 'b', 'level': 1, 'parent': 'c', 'children': ['d'], 'entry-id': None}
    },
    {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': None, 'entry-id': None, 'x': 'y'}},
    {'a': {'name': 2, 'level': 1, 'parent': 'c', 'children': None, 'entry-id': None}},
    {'a': {'name': '', 'level': 1, 'parent': 'c', 'children': None, 'entry-id': None}},
    {'a': {'name': None, 'level': 1, 'parent': 'c', 'children': None, 'entry-id': None}},
    {'a': {'name': 'b', 'level': '1', 'parent': 'c', 'children': None, 'entry-id': None}},
    {'a': {'name': 'b', 'level': None, 'parent': 'c', 'children': None, 'entry-id': None}},
    {'a': {'name': 'b', 'level': 0, 'parent': 'c', 'children': None, 'entry-id': None}},
    {'a': {'name': 'b', 'level': 1, 'parent': '', 'children': None, 'entry-id': None}},
    {'a': {'name': 'b', 'level': 1, 'parent': 2, 'children': None, 'entry-id': None}},
    {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': [], 'entry-id': None}},
    {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': [1], 'entry-id': None}},
    {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': [''], 'entry-id': None}},
    {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': ['a'], 'entry-id': 1}},
    {'a': {'name': 'b', 'level': 1, 'parent': 'c', 'children': ['a'], 'entry-id': ''}}
]
@pt.mark.parametrize('invalid_json_object', test_invalid_load_from_json_data)
def test_invalid_load_from_json(caplog, json_file_path: str, invalid_json_object: t.Union[list, dict, int, float, str]):
    expected_error_message = f'Failed to load the hierarchy nodes. The pathway organizer JSON file at {json_file_path} is ' \
                             f'corrupted and will need to be re-created.'

    u.test_invalid_load_from_json(
        json_file_path=json_file_path, invalid_json_object=invalid_json_object, method=po.PathwayOrganizer.load_from_json,
        expected_error_message=expected_error_message, caplog=caplog
    )
