"""
Usage:
    kegg_pull entry-ids -h | --help
    kegg_pull entry-ids from-database <database-name> [--output=<output-location>] [--file=<file-name>]
    kegg_pull entry-ids from-file <file-path> [--output=<output-location>] [--file=<file-name>]
    kegg_pull entry-ids from-keywords <database-name> <keywords> [--output=<output-location>] [--file=<file-name>]
    kegg_pull entry-ids from-molecular-attribute <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output-location>] [--file=<file-name>]

Options:
    -h --help                               Show this help message.
    from-database                           Pulls all the entry IDs within a given database.
    <database-name>                         The KEGG database from which to pull a list of entry IDs.
    --output=<output-location>              The location (either a directory or ZIP archive if ends in '.zip') of the file to store the output (1 entry ID per line). Prints to the console if not set.
    --file=<file-name>                      The name of the file to store in the output location (specified by --output). If --output is set but --file is not set, defaults to file name of "entry-ids.txt".
    from-file                               Loads the entry IDs from a file.
    <file-path>                             Path to a file containing a list of entry IDs with one entry ID on each line.
    from-keywords                           Searches for entries within a database based on provided keywords.
    <keywords>                              Comma separated list of keywords to search within entries (e.g. --keywords=kw1,k2w,kw3 etc.).
    from-molecular-attribute                Searches a database of molecule-type KEGG entries by molecular attributes.
    --formula=<formula>                     Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searchers for molecule entries containing 5 oxygen atoms and/or 7 carbon atoms).
    --exact-mass=<exact-mass>               Either a single number (e.g. --exact-mass=155.5) or two numbers (e.g. --exact-mass=155.5 --exact-mass=244.4). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
    --molecular-weight=<molecular-weight>   Same as --exact-mass but searches based on the molecular weight.
"""
import docopt as d

from . import entry_ids as ei
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    database_name: str = args['<database-name>']
    entry_ids_getter = ei.EntryIdsGetter()

    if args['from-database']:
        entry_ids: list = entry_ids_getter.from_database(database_name=database_name)
    elif args['from-file']:
        entry_ids_file_path: str = args['<file-path>']
        entry_ids: list = ei.EntryIdsGetter.from_file(file_path=entry_ids_file_path)
    elif args['from-keywords']:
        keywords: str = args['<keywords>']
        keywords: list = u.split_comma_separated_list(list_string=keywords)
        entry_ids: list = entry_ids_getter.from_keywords(database_name=database_name, keywords=keywords)
    else:
        formula, exact_mass, molecular_weight = u.get_molecular_attribute_args(args=args)

        entry_ids: list = entry_ids_getter.from_molecular_attribute(
            database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
        )

    output_location: str = args['--output']
    file_name: str = args['--file']
    file_name: str = 'entry-ids.txt' if file_name is None and output_location is not None else file_name
    entry_ids: str = '\n'.join(entry_ids)
    u.handle_cli_output(output_location=output_location, output_content=entry_ids, file_name=file_name, save_type='w')
