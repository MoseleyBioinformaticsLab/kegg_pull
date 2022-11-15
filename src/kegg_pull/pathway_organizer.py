from . import rest as r

import json as js


class PathwayOrganizer:
    def __init__(self, kegg_rest: r.KEGGrest = None) -> None:
        self._hierarchy_nodes = None
        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()

    @property
    def hierarchy_nodes(self) -> dict:
        return self._hierarchy_nodes

    def parse_from_kegg(self) -> None:
        self._hierarchy_nodes = {}
        hierarchy: list = self._get_hierarchy()
        self._parse_hierarchy(level=1, hierarchy_nodes=hierarchy, parent_name=None)

    def _get_hierarchy(self) -> list:
        kegg_response: r.KEGGresponse = self._kegg_rest.get(entry_ids=['br:br08901'], entry_field='json')
        text_body: str = kegg_response.text_body.strip()
        brite_hierarchy: dict = js.loads(s=text_body)

        return brite_hierarchy['children']

    def _parse_hierarchy(self, level: int, hierarchy_nodes: list, parent_name: str) -> set:
        nodes_added = set()

        for hierarchy_node in hierarchy_nodes:
            node_name: str = hierarchy_node['name']

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
        key: str = entry_id if entry_id is not None else name

        assert key not in self._hierarchy_nodes.keys(), f'Duplicate brite hierarchy node name {key}'

        self._hierarchy_nodes[key] = {'name': name, 'level': level, 'parent': parent, 'children': children, 'entry-id': entry_id}

        return key


class MetabolicPathwayOrganizer(PathwayOrganizer):
    def _get_hierarchy(self) -> list:
        complete_hierarchy: list = super(MetabolicPathwayOrganizer, self)._get_hierarchy()
        hierarchy = None

        for hierarchy_node in complete_hierarchy:
            if hierarchy_node['name'] == 'Metabolism':
                hierarchy: list = hierarchy_node['children']

                break

        hierarchy = [hierarchy_node for hierarchy_node in hierarchy if hierarchy_node['name'] != 'Global and overview maps']

        return hierarchy
