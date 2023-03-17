"""
Flattening A Pathways Brite Hierarchy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for flattening a pathways Brite hierarchy (ID: 'br:br08901') into a collection of its nodes, mapping a node ID to information about it, enabling combinations with other KEGG data.
"""
import json
import logging as log
import typing as t
from . import rest as r
from . import _utils as u

RawHierarchyNode = t.TypedDict('RawHierarchyNode', {'name': str, 'children': list[dict] | None})
HierarchyNode = t.TypedDict(
    'HierarchyNode', {'name': str, 'level': int, 'parent': str | None, 'children': list[str] | None, 'entry_id': str | None})
HierarchyNodes = dict[str, HierarchyNode]


class PathwayOrganizer(u.NonInstantiable):
    """
    Contains methods for managing a mapping of node keys to node information, these nodes coming from a pathways Brite hierarchy.
    An instantiated ``PathwayOrganizer`` object must be returned from either ``PathwayOrganizer.load_from_kegg`` or
    ``PathwayOrganizer.load_from_json``. The ``__init__`` is not meant to be called directly. The ``__str__`` method returns a JSON
    string of ``hierarchy_nodes``.

    :ivar dict hierarchy_nodes: The mapping of node keys to node information managed by the PathwayOrganizer. The node information fields include:

                - **name**: The name of the node obtained directly from the Brite hierarchy.
                - **level**: The level that the node appears in the hierarchy.
                - **parent**: The key (not the name) of the parent node (None if top level node).
                - **children**: The keys (not the names) of the node's children (None if leaf node).
                - **entry_id**: The entry ID of the node (None if the node does not correspond to a KEGG entry).
    """
    def __init__(self) -> None:
        super(PathwayOrganizer, self).__init__()
        self.hierarchy_nodes: HierarchyNodes | None = None
        self._filter_nodes: set[str] | None = None

    @staticmethod
    def load_from_kegg(
            top_level_nodes: set[str] | None = None, filter_nodes: set[str] | None = None,
            kegg_rest: r.KEGGrest | None = None):
        """ Pulls the Brite hierarchy from the KEGG REST API and converts it to the hierarchy_nodes mapping.

        :param top_level_nodes: Node names in the highest level of the hierarchy to select from. If None, all top level nodes are traversed to create the hierarchy_nodes.
        :param filter_nodes: Names (not keys) of nodes to exclude from the hierarchy_nodes mapping. Neither these nodes nor any of their children will be included.
        :param kegg_rest: Optional KEGGrest object for obtaining the Brite hierarchy. A new KEGGrest object is created by default.
        :returns PathwayOrganizer: The resulting PathwayOrganizer object.
        """
        pathway_org = PathwayOrganizer()
        pathway_org.hierarchy_nodes = HierarchyNodes()
        pathway_org._filter_nodes = filter_nodes
        hierarchy = PathwayOrganizer._get_hierarchy(kegg_rest=kegg_rest)
        valid_top_level_nodes = sorted(top_level_node['name'] for top_level_node in hierarchy)
        if top_level_nodes is not None:
            for top_level_node in list(top_level_nodes):
                if top_level_node not in valid_top_level_nodes:
                    log.warning(
                        f'Top level node name "{top_level_node}" is not recognized and will be ignored. Valid values are: '
                        f'"{", ".join(valid_top_level_nodes)}"')
                    top_level_nodes.remove(top_level_node)
            hierarchy = [top_level_node for top_level_node in hierarchy if top_level_node['name'] in top_level_nodes]
        pathway_org._parse_hierarchy(level=1, raw_hierarchy_nodes=hierarchy, parent_name=None)
        return pathway_org

    @staticmethod
    def _get_hierarchy(kegg_rest: r.KEGGrest | None) -> list[RawHierarchyNode]:
        """ Pulls the Brite hierarchy (to be converted to hierarchy_nodes) from the KEGG REST API.

        :return: The list of top level nodes that branch out into the rest of the hierarchy until reaching leaf nodes.
        """
        kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()
        kegg_response = kegg_rest.get(entry_ids=['br:br08901'], entry_field='json')
        text_body = kegg_response.text_body.strip()
        brite_hierarchy: dict = json.loads(s=text_body)
        return brite_hierarchy['children']

    def _parse_hierarchy(self, level: int, raw_hierarchy_nodes: list[RawHierarchyNode], parent_name: str | None) -> set[str]:
        """ Recursively traverses the Brite hierarchy to create the hierarchy_nodes mapping.

        :param level: The current level of recursion representing the level of the node in the hierarchy.
        :param raw_hierarchy_nodes: The list of nodes in the current branch of the hierarchy being traversed.
        :param parent_name: The node key of the parent node of the current branch of the hierarchy.
        :return: The keys of the nodes added to the hierarchy_nodes property representing the children of the parent node.
        """
        nodes_added = set[str]()
        for raw_hierarchy_node in raw_hierarchy_nodes:
            node_name = raw_hierarchy_node['name']
            if self._filter_nodes is None or node_name not in self._filter_nodes:
                if 'children' in raw_hierarchy_node.keys():
                    node_children = self._parse_hierarchy(
                        level=level+1, raw_hierarchy_nodes=raw_hierarchy_node['children'], parent_name=node_name)
                    if self._filter_nodes is not None:
                        expected_n_children_added = len(
                            [child for child in raw_hierarchy_node['children'] if child['name'] not in self._filter_nodes])
                    else:
                        expected_n_children_added = len(raw_hierarchy_node['children'])
                    assert len(node_children) == expected_n_children_added, f'Not all children added for node: {node_name}'
                    node_key = self._add_hierarchy_node(
                        name=node_name, level=level, parent=parent_name, children=node_children, entry_id=None)
                else:
                    entry_id = node_name.split(' ')[0]
                    entry_id = f'path:map{entry_id}'
                    node_key = self._add_hierarchy_node(
                        name=node_name, level=level, parent=parent_name, children=None, entry_id=entry_id)
                nodes_added.add(node_key)
        return nodes_added

    def _add_hierarchy_node(self, name: str, level: int, parent: str, children: set[str] | None, entry_id: str | None) -> str:
        """ Adds a Brite hierarchy node representation to the hierarchy_nodes property.

        :param name: The name of the node obtained directly from the Brite hierarchy.
        :param level: The level that the node appears in the hierarchy.
        :param parent: The key of the parent node (None if top level node).
        :param children: The keys of the node's children (None if leaf node).
        :param entry_id: The entry ID of the node; string if it represents a KEGG pathway mapping, else None.
        :return: The key chosen for the node, equal to its entry ID if not None, else the name of the Node.
        """
        key = entry_id if entry_id is not None else name
        assert key not in self.hierarchy_nodes.keys(), f'Duplicate brite hierarchy node name {key}'
        children = sorted(children) if children is not None else None
        self.hierarchy_nodes[key] = HierarchyNode(name=name, level=level, parent=parent, children=children, entry_id=entry_id)
        return key

    def __str__(self) -> str:
        """ Converts the hierarchy nodes to a JSON string.

        :return: The JSON string version of the hierarchy nodes.
        """
        return json.dumps(self.hierarchy_nodes, indent=2)

    _schema = {
        'type': 'object',
        'minProperties': 1,
        'additionalProperties': False,
        'patternProperties': {
            '^.+$': {
                'type': 'object',
                'required': ['name', 'level', 'parent', 'children', 'entry_id'],
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
                        'type': ['array', 'null'],
                        'items': {
                            'type': 'string',
                            'minLength': 1
                        }
                    },
                    'entry_id': {
                        'type': ['string', 'null'],
                        'minLength': 1
                    }
                }
            }
        }
    }

    @staticmethod
    def load_from_json(file_path: str):
        """ Loads the hierarchy_nodes mapping that was cached in a JSON file using load_from_kegg followed by save_to_json.

        :param file_path: Path to the JSON file. If reading from a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:hierarchy-nodes.json).
        :returns PathwayOrganizer: The resulting PathwayOrganizer object.
        :raises ValidationError: Raised if the JSON file does not follow the correct JSON schema. Should follow the correct schema if hierarchy_nodes was cached using load_from_kegg followed by save_to_json.
        """
        pathway_org = PathwayOrganizer()
        hierarchy_nodes: HierarchyNodes = u.load_json_file(
            file_path=file_path, json_schema=PathwayOrganizer._schema,
            validation_error_message=f'Failed to load the hierarchy nodes. The pathway organizer JSON file at {file_path} is '
                                     f'corrupted and will need to be re-created.')
        pathway_org.hierarchy_nodes = hierarchy_nodes
        return pathway_org

    def save_to_json(self, file_path: str) -> None:
        """ Saves the hierarchy_nodes mapping to a JSON file to cache it.

        :param file_path: The path to the JSON file to save the hierarchy_nodes mapping. If saving in a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:hierarchy-nodes.json).
        """
        json_string = str(self)
        u.save_output(output_target=file_path, output_content=json_string)
