"""
Flattening A Pathways Brite Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Contains classes for flattening a pathways Brite hierarchy (ID: 'br:br08901') into a collection of its nodes, mapping a node ID to information about it, enabling combinations with other KEGG data.
"""
from . import rest as r
from . import _utils as u

import json as j
import logging as l


class PathwayOrganizer:
    """
    Contains methods for creating and storing a hierarchy nodes mapping of node keys to node information from a pathways Brite
    hierarchy. The hierarchy_nodes property is None at first and must be instantiated either from parse_from_kegg() or load_json().
    """
    def __init__(self, kegg_rest: r.KEGGrest = None) -> None:
        """
        :param kegg_rest: Optional KEGGrest object for obtaining the Brite hierarchy. A new KEGGrest object is created by default.
        """
        self._hierarchy_nodes: dict = None
        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()
        self._filter_nodes: set = None

    @property
    def hierarchy_nodes(self) -> dict:
        """
        None at first and must be instantiated either from parse_from_kegg() or load_json(). The property is a dictionary mapping
        node keys (string) each to a dictionary with the following properties:
        name: The name of the node obtained directly from the Brite hierarchy.
        level: The level that the node appears in the hierarchy.
        parent: The key of the parent node (None if top level node).
        children: The keys of the node's children (None if leaf node).
        entry_id: The entry ID of the node; string if it represents a KEGG pathway mapping, else None.
        """
        return self._hierarchy_nodes

    def load_from_kegg(self, top_level_nodes: set = None, filter_nodes: set = None) -> None:
        """ Pulls the Brite hierarchy from the KEGG REST API and converts it to the hierarchy_nodes mapping.

        :param top_level_nodes: Node names in the highest level of the hierarchy to select from. If None, all top level nodes are traversed to create the hierarchy_nodes.
        :param filter_nodes: Names (not keys) of nodes to exclude from the hierarchy_nodes mapping. Neither these nodes nor any of their children will be included.
        """
        self._hierarchy_nodes = {}
        self._filter_nodes = filter_nodes
        hierarchy: list = self._get_hierarchy()
        valid_top_level_nodes: set = {top_level_node['name'] for top_level_node in hierarchy}

        if top_level_nodes is not None:
            for top_level_node in list(top_level_nodes):
                if top_level_node not in valid_top_level_nodes:
                    l.warning(f'Top level node name "{top_level_node}" is not recognized and will be ignored.')
                    top_level_nodes.remove(top_level_node)

            hierarchy: list = [top_level_node for top_level_node in hierarchy if top_level_node['name'] in top_level_nodes]

        self._parse_hierarchy(level=1, hierarchy_nodes=hierarchy, parent_name=None)

    def _get_hierarchy(self) -> list:
        """ Pulls the Brite hierarchy (to be converted to hierarchy_nodes) from the KEGG REST API.

        :return: The list of top level nodes that branch out into the rest of the hierarchy until reaching leaf nodes.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.get(entry_ids=['br:br08901'], entry_field='json')
        text_body: str = kegg_response.text_body.strip()
        brite_hierarchy: dict = j.loads(s=text_body)

        return brite_hierarchy['children']

    def _parse_hierarchy(self, level: int, hierarchy_nodes: list, parent_name: str) -> set:
        """ Recursively traverses the Brite hierarchy to create the hierarchy_nodes mapping.

        :param level: The current level of recursion representing the level of the node in the hierarchy.
        :param hierarchy_nodes: The list of nodes in the current branch of the hierarchy being traversed.
        :param parent_name: The node key of the parent node of the current branch of the hierarchy.
        :return: The keys of the nodes added to the hierarchy_nodes property representing the children of the parent node.
        """
        nodes_added = set()

        for hierarchy_node in hierarchy_nodes:
            node_name: str = hierarchy_node['name']

            if self._filter_nodes is not None and node_name not in self._filter_nodes:
                if 'children' in hierarchy_node.keys():
                    node_children: set = self._parse_hierarchy(
                        level=level+1, hierarchy_nodes=hierarchy_node['children'], parent_name=node_name
                    )

                    assert len(node_children) == len(hierarchy_node['children']), f'Not all children added for node: {node_name}'

                    node_key: str = self._add_hierarchy_node(
                        name=node_name, level=level, parent=parent_name, children=node_children, entry_id=None
                    )
                else:
                    entry_id: str = node_name.split(' ')[0]
                    entry_id = f'path:map{entry_id}'

                    node_key: str = self._add_hierarchy_node(
                        name=node_name, level=level, parent=parent_name, children=None, entry_id=entry_id
                    )

                nodes_added.add(node_key)

        return nodes_added

    def _add_hierarchy_node(self, name: str, level: int, parent: str, children: set, entry_id: str) -> str:
        """ Adds a Brite hierarchy node representation to the hierarchy_nodes property.

        :param name: The name of the node obtained directly from the Brite hierarchy.
        :param level: The level that the node appears in the hierarchy.
        :param parent: The key of the parent node (None if top level node).
        :param children: The keys of the node's children (None if leaf node).
        :param entry_id: The entry ID of the node; string if it represents a KEGG pathway mapping, else None.
        :return: The key chosen for the node, equal to its entry ID if not None, else the name of the Node.
        """
        key: str = entry_id if entry_id is not None else name

        assert key not in self._hierarchy_nodes.keys(), f'Duplicate brite hierarchy node name {key}'

        self._hierarchy_nodes[key] = {'name': name, 'level': level, 'parent': parent, 'children': children, 'entry-id': entry_id}

        return key

    def _check_hierarchy_nodes_loaded(self) -> None:
        """ Determines if the hierarchy nodes have been loaded and raises an exception otherwise."""
        if self._hierarchy_nodes is None:
            raise ValueError('The hierarchy nodes have node been loaded yet. Use either load_from_kegg or load_from_json')

    def __str__(self) -> str:
        """ Converts the hierarchy nodes to a JSON string.

        :return: The JSON string version of the hierarchy nodes.
        """
        self._check_hierarchy_nodes_loaded()

        for node_key, node in self._hierarchy_nodes.items():
            node['children'] = sorted(node['children'])

        return j.dumps(self._hierarchy_nodes, indent=1)

    def load_from_json(self, file_path: str) -> None:
        """ Loads the hierarchy_nodes property from a JSON file. Re-creates the hierarchy_nodes via parse_from_kegg() if the JSON
        file doesn't follow the correct schema.

        :param file_path: Path to the JSON file. If reading from a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:hierarchy-nodes.json).
        """
        schema = {
            'type': 'object',
            'minProperties': 1,
            'additionalProperties': False,
            'patternProperties': {
                '^.+$': {
                    'type': 'object',
                    'required': ['name', 'level', 'parent', 'children', 'entry-id'],
                    'additionalProperties': False,
                    'properties': {
                        'name': {
                            'type': 'string',
                            'minLength': 1
                        },
                        'level': {
                            'type': 'integer',
                            'minimum': 1
                        },
                        'parent': {
                            'type': ['string', 'null'],
                            'minLength': 1
                        },
                        'children': {
                            'minItems': 1,
                            'type': ['array', 'null']
                        },
                        'entry-id': {
                            'type': ['string', 'null'],
                            'minLength': 1
                        }
                    }
                }
            }
        }

        hierarchy_nodes: dict = u.load_json_file(
            file_path=file_path, json_schema=schema,
            validation_error_message=f'Failed to load the hierarchy nodes. The pathway organizer JSON file at {file_path} is corrupted and will need to be re-created.'
        )

        self._hierarchy_nodes = hierarchy_nodes

    def save_to_json(self, file_path: str) -> None:
        """ Saves the hierarchy_nodes property to a JSON file.

        :param file_path: The path to the JSON file to save the hierarchy_nodes mapping. If saving in a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:hierarchy-nodes.json).
        """
        self._check_hierarchy_nodes_loaded()
        json_string: str = str(self)
        u.save_output(output_target=file_path, output_content=json_string)
