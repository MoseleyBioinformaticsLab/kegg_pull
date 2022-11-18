"""
Usage:
    kegg_pull pathway-organizer [--top-level-nodes] [--filter-nodes] [--output=<output>] [--zip-file=<zip-file>]

Options:
    -h --help               Show this help message.
    --top-level-nodes       Node names in the highest level of the hierarchy to select from. If None, all top level nodes are traversed to create the mapping of node key to node info.
    --filter-nodes          Names (not keys) of nodes to exclude from the mapping of node key to node info. Neither these nodes nor any of their children will be included.
    --output=<output>       The file to store the flattened Brite hierarchy as a JSON structure with node keys mapping to node info, either a JSON file or ZIP archive. Prints to the console if not set. If ends in ".zip", saves file in a zip archive.
    --zip-file=<zip-file>   The name of the file to store in a zip archive. If not set, defaults to saving a file with the same name as the zip archive minus the .zip extension. Ignored if --output does not end in ".zip".
"""
import docopt as d

from . import pathway_organizer as po
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    pathway_organizer = po.PathwayOrganizer()
    pathway_organizer.load_from_kegg(top_level_nodes=args['--top-level-nodes'], filter_nodes=args['--filter-nodes'])
    hierarchy_nodes_json_string = str(pathway_organizer)

    u.handle_cli_output(
        output_path=args['--output'], output_string=hierarchy_nodes_json_string, zip_file_name=args['--zip-file'], save_type='w'
    )
