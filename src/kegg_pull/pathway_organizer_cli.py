"""
Usage:
    kegg_pull pathway-organizer [--tln=<top-level-nodes>] [--fn=<filter-nodes>] [--output=<output>]

Options:
    -h --help               Show this help message.
    --tln=<top-level-nodes> Node names in the highest level of the hierarchy to select from. If not set, all top level nodes are traversed to create the mapping of node key to node info. Either a comma separated list (e.g. node1,node2,node3 etc.) or if equal to "-", read from standard input one node per line; Press CTRL+D to finalize input or pipe (e.g. cat nodes.txt | kegg_pull pathway-organizer --tln=- ...). If both "--tln" and "--fn" are set as "-", one of the lines must be the delimiter "---" without quotes in order to distinguish the input, with the top level nodes first and filter nodes second.
    --fn=<filter-nodes>     Names (not keys) of nodes to exclude from the mapping of node key to node info. Neither these nodes nor any of their children will be included. If not set, no nodes will be excluded. Either a comma separated list (e.g. node1,node2,node3 etc.) or if equal to "-", read from standard input one node per line; Press CTRL+D to finalize input or pipe (e.g. cat nodes.txt | kegg_pull pathway-organizer --fn=- ...). If both "--tln" and "--fn" are set as "-", one of the lines must be the delimiter "---" without quotes in order to distinguish the input, with the top level nodes first and filter nodes second.
    --output=<output>       The file to store the flattened Brite hierarchy as a JSON structure with node keys mapping to node info, either a JSON file or ZIP archive. Prints to the console if not set. If saving to a ZIP archive, the file path must be in the form of /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
"""
import docopt as d
import sys
from . import pathway_organizer as po
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    if args['--tln'] == '-' and args['--fn'] == '-':
        # If both the top level nodes and filter nodes are coming from standard input, convert them to comma separated lists
        inputs: str = sys.stdin.read()
        [top_level_nodes, filter_nodes] = inputs.split('---\n')
        top_level_nodes: str = ','.join(top_level_nodes.strip().split('\n'))
        filter_nodes: str = ','.join(filter_nodes.strip().split('\n'))
        top_level_nodes: set = set(u.parse_input_sequence(input_source=top_level_nodes))
        filter_nodes: set = set(u.parse_input_sequence(input_source=filter_nodes))
    else:
        top_level_nodes: str = args['--tln']
        filter_nodes: str = args['--fn']
        if top_level_nodes:
            top_level_nodes: set = set(u.parse_input_sequence(input_source=top_level_nodes))
        if filter_nodes:
            filter_nodes: set = set(u.parse_input_sequence(input_source=filter_nodes))
    pathway_organizer = po.PathwayOrganizer.load_from_kegg(top_level_nodes=top_level_nodes, filter_nodes=filter_nodes)
    hierarchy_nodes_json_string = str(pathway_organizer)
    u.print_or_save(output_target=args['--output'], output_content=hierarchy_nodes_json_string)
