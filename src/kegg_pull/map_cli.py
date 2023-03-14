"""
Usage:
    kegg_pull map -h | --help
    kegg_pull map <source-database> <target-database> [--deduplicate] [--add-glycans] [--add-drugs] [--output=<output>]
    kegg_pull map entry-ids <entry-ids> <target-database> [--reverse] [--output=<output>]
    kegg_pull map <source-database> <intermediate-database> <target-database> [--deduplicate] [--add-glycans] [--add-drugs] [--output=<output>]

Options:
    -h --help               Show this help message.
    <source-database>       The name of the database with entry IDs mapped to the target database.
    <target-database>       The name of the database with entry IDs mapped from the source database.
    --deduplicate           Some mappings including pathway entry IDs result in half beginning with the normal "path:map" prefix but the other half with a different prefix. If set, removes the IDs corresponding to identical entries but with a different prefix. Raises an exception if the source database is not "pathway". If both a target database of "pathway" and deduplication is desired, set the source databae to "pathway" and set the --reverse flag.
    --add-glycans           Whether to add the corresponding compound IDs of equivalent glycan entries. Logs a warning if the source database is not "compound". If both a target database of "compound" and added glycans is desired, set the source database to "compound" and set the --reverse flag.
    --add-drugs             Whether to add the corresponding compound IDs of equivalent drug entries. Logs a warning if the source database is not "compound". If both a target database of "compound" and added drugs is desired, set the source database to "compound" and set the --reverse flag.
    --reverse               Reverses the mapping with the target becoming the source and the source becoming the target.
    --output=<output>       The location (either a directory or ZIP archive) of the JSON file to store the mapping. If not set, prints a JSON representation of the mapping to the console. If a ZIP archive, the file path must be in the form of /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
    entry-ids               Find cross-references to a target database from a list of specific entry IDs.
    <entry-ids>             Comma separated list of entry IDs (e.g. Id1,Id2,Id3 etc.). Or if equal to "-", entry IDs are read from standard input, one entry ID per line; Press CTRL+D to finalize input or pipe (e.g. cat file.txt | kegg_pull map entry-ids drug - ...).
    <intermediate-database> The name of an intermediate database with which to find cross-references to cross-references e.g. "kegg_pull map ko reaction compound" creates a mapping from ko-to-compound via ko-to-reaction cross-references connected to reaction-to-compound cross-references
"""
import docopt as doc

from . import map as kmap
from . import _utils as u


def main():
    args: dict = doc.docopt(__doc__)
    source_database: str = args['<source-database>']
    intermediate_database: str = args['<intermediate-database>']
    target_database: str = args['<target-database>']
    deduplicate: bool = args['--deduplicate']
    add_glycans: bool = args['--add-glycans']
    add_drugs: bool = args['--add-drugs']
    if args['entry-ids']:
        reverse: bool = args['--reverse']
        entry_ids: list = u.parse_input_sequence(input_source=args['<entry-ids>'])
        mapping: dict = kmap.entries_map(
            entry_ids=entry_ids, target_database=target_database, reverse=reverse)
    elif intermediate_database:
        mapping: dict = kmap.indirect(
            source_database=source_database, intermediate_database=intermediate_database,
            target_database=target_database, deduplicate=deduplicate, add_glycans=add_glycans, add_drugs=add_drugs)
    else:
        mapping: dict = kmap.database_map(
            source_database=source_database, target_database=target_database, deduplicate=deduplicate,
            add_glycans=add_glycans, add_drugs=add_drugs)
    mapping: str = kmap.to_json_string(mapping=mapping)
    u.print_or_save(output_target=args['--output'], output_content=mapping)
