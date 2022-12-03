"""
Usage:
    kegg_pull link-to-dict -h | --help
    kegg_pull link-to-dict <target-database-name> <source-database-name> [--output=<output>]
    kegg_pull link-to-dict --link-target=<target-database-name> <entry-ids> [--output=<output>]
    kegg_pull link-to-dict pathway-to-compound [--add-glycans] [--add-drugs] [--output=<output>]
    kegg_pull link-to-dict reaction-to-compound [--add-glycans] [--output=<output>]
    kegg_pull link-to-dict gene-to-compound [--add-glycans] [--output=<output>]
    kegg_pull link-to-dict compound-to-pathway [--add-glycans] [--output=<output>]
    kegg_pull link-to-dict compound-to-reaction [--add-glycans] [--output=<output>]
    kegg_pull link-to-dict compound-to-gene [--add-glycans] [--output=<output>]
    kegg_pull link-to-dict pathway-to-gene [--output=<output>]
    kegg_pull link-to-dict pathway-to-reaction [--output=<output>]
    kegg_pull link-to-dict gene-to-pathway [--output=<output>]
    kegg_pull link-to-dict reaction-to-pathway [--output=<output>]
    kegg_pull link-to-dict reaction-to-gene [--output=<output>]
    kegg_pull link-to-dict gene-to-reaction [--output=<output>]

Options:
    -h --help                               Show this help message.
    <target-database-name>                  The name of the database to find cross-references in the source database.
    <source-database-name>                  The name of the database from which cross-references are found in the target database.
    --output=<output>                       The location (either a directory or ZIP archive) of the JSON file to store the mapping. If not set, prints a JSON representation of the mapping to the console. If a ZIP archive, the file path must be in the form of /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
    --link-target=<target-database-name>    The name of the database to find cross-references in the provided entry IDs.
    <entry-ids>                             Comma separated list of entry IDs (e.g. Id1,Id2,Id3 etc.). Or if equal to "-", entry IDs are read from standard input, one entry ID per line; Press CTRL+D to finalize input or pipe (e.g. cat file.txt | kegg_pull link-to-dict --link-target=drug - ...).
    pathway-to-compound                     Creates a specific mapping of KEGG entry IDs.
    --add-glycans                           Whether to add the compound IDs corresponding to KEGG glycan entries.
    --add-drugs                             Whether to add the compound IDs corresponding to KEGG drug entries.
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

from . import link_to_dict as ltd
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    add_glycans: bool = args['--add-glycans']
    add_drugs: bool = args['--add-drugs']

    if args['pathway-to-compound']:
        mapping: dict = ltd.pathway_to_compound(add_glycans=add_glycans, add_drugs=add_drugs)
    elif args['reaction-to-compound']:
        mapping: dict = ltd.reaction_to_compound(add_glycans=add_glycans, add_drugs=add_drugs)
    elif args['gene-to-compound']:
        mapping: dict = ltd.gene_to_compound(add_glycans=add_glycans, add_drugs=add_drugs)
    elif args['compound-to-pathway']:
        mapping: dict = ltd.compound_to_pathway(add_glycans=add_glycans, add_drugs=add_drugs)
    elif args['compound-to-reaction']:
        mapping: dict = ltd.compound_to_reaction(add_glycans=add_glycans, add_drugs=add_drugs)
    elif args['compound-to-gene']:
        mapping: dict = ltd.compound_to_gene(add_glycans=add_glycans, add_drugs=add_drugs)
    elif args['pathway-to-gene']:
        mapping: dict = ltd.pathway_to_gene()
    elif args['pathway-to-reaction']:
        mapping: dict = ltd.pathway_to_reaction()
    elif args['gene-to-pathway']:
        mapping: dict = ltd.gene_to_pathway()
    elif args['reaction-to-pathway']:
        mapping: dict = ltd.reaction_to_pathway()
    elif args['reaction-to-gene']:
        mapping: dict = ltd.reaction_to_gene()
    elif args['gene-to-reaction']:
        mapping: dict = ltd.gene_to_reaction()
    elif args['<target-database-name>']:
        mapping: dict = ltd.database_link(
            target_database_name=args['<target-database-name>'], source_database_name=args['source-database-name']
        )
    else:
        entry_ids: list = u.parse_input_sequence(input_source=args['<entry-ids>'])
        mapping: dict = ltd.entries_link(target_database_name=args['--link-target'], entry_ids=entry_ids)

    mapping: str = ltd.to_json_string(mapping=mapping)
    u.print_or_save(output_target=args['--output'], output_content=mapping)
