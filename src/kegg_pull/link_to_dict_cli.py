"""
Usage:
    kegg_pull link-to-dict -h | --help
    kegg_pull link-to-dict <target-database-name> <source-database-name> [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict --link-target=<target-database-name> <entry-ids> [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict pathway-to-compound [--add-glycans] [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict reaction-to-compound [--add-glycans] [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict gene-to-compound [--add-glycans] [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict compound-to-pathway [--add-glycans] [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict compound-to-reaction [--add-glycans] [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict compound-to-gene [--add-glycans] [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict pathway-to-gene [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict pathway-to-reaction [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict gene-to-pathway [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict reaction-to-pathway [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict reaction-to-gene [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull link-to-dict gene-to-reaction [--output=<output>] [--zip-file=<zip-file>]

Options:
    -h --help                               Show this help message.
    <target-database-name>                  The name of the database to find cross-references in the source database.
    <source-database-name>                  The name of the database from which cross-references are found in the target database.
    --output=<output>                       The file to store the mapping, either a JSON file or ZIP archive. Prints to the console if not set. If ends in ".zip", saves file in a zip archive.
    --zip-file=<zip-file>                   The name of the JSON file to store in a zip archive. If not set, defaults to saving a file with the same name as the ZIP archive minus the .zip extension. Ignored if --output does not end in ".zip".
    --link-target=<target-database-name>    The name of the database to find cross-references in the provided entry IDs.
    <entry-ids>                             Comma separated list of entry IDs.
    pathway-to-compound                     Creates a specific mapping of KEGG entry IDs.
    --add-glycans                           Whether to add the compound IDs corresponding to KEGG glycan entries.
    reaction-to-compound                    Creates a specific mapping of KEGG entry IDs.
    gene-to-compound                        Creates a specific mapping of KEGG entry IDs.
    compound-to-pathway                     Creates a specific mapping of KEGG entry IDs.
    compound-to-reaction                    Creates a specific mapping of KEGG entry IDs.
    compound-to-gene                        Creates a specific mapping of KEGG entry IDs.
    pathway-to-gene                         Creates a specific mapping of KEGG entry IDs.
    pathway-to-reaction                     Creates a specific mapping of KEGG entry IDs.
    gene-to-pathway                         Creates a specific mapping of KEGG entry IDs.
    reaction-to-pathway                     Creates a specific mapping of KEGG entry IDs.
    reaction-to-gene                        Creates a specific mapping of KEGG entry IDs.
    gene-to-reaction                        Creates a specific mapping of KEGG entry IDs.
"""
import docopt as d
import json as j

from . import link_to_dict as ltd
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    add_glycans: bool = args['--add-glycans']
    link_to_dict = ltd.LinkToDict()

    if args['pathway-to-compound']:
        mapping: dict = link_to_dict.pathway_to_compound(add_glycans=add_glycans)
    elif args['reaction-to-compound']:
        mapping: dict = link_to_dict.reaction_to_compound(add_glycans=add_glycans)
    elif args['gene-to-compound']:
        mapping: dict = link_to_dict.gene_to_compound(add_glycans=add_glycans)
    elif args['compound-to-pathway']:
        mapping: dict = link_to_dict.compound_to_pathway(add_glycans=add_glycans)
    # TODO Fill in the rest of the specific mappings
    elif args['<target-database-name']:
        mapping: dict = link_to_dict.database_link(
            target_database_name=args['<target-database-name>'], source_database_name=args['source-database-name']
        )
    else:
        entry_ids: list = u.split_comma_separated_list(list_string=args['<entry-ids>'])
        mapping: dict = link_to_dict.entries_link(target_database_name=args['--link-target'], entry_ids=entry_ids)

    mapping: str = j.dumps(obj=mapping, indent=1)
    u.handle_cli_output(output_path=args['--output'], output_string=mapping, zip_file_name=args['--zip-file'], save_type='w')
