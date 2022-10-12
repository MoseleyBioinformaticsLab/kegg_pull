"""
Usage:
    kegg_pull entry-ids -h | --help
    kegg_pull entry-ids from-database <database-name> [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull entry-ids from-file <file-path> [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull entry-ids from-keywords <database-name> <keywords> [--output=<output>] [--zip-file=<zip-file>]
    kegg_pull entry-ids from-molecular-attribute <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>] [--zip-file=<zip-file>]

Options:
    -h --help                               Show this help message.
    from-database                           Pulls all the entry IDs within a given database.
    <database-name>                         The KEGG database from which to pull a list of entry IDs.
    --output=<output>                       Path to the file to store the output (1 entry ID per line). Prints to the console if not specified. If ends in ".zip", saves file to a zip archive.
    --zip-file=<zip-file>                   The name of the file to store in a zip archive. If not set, defaults to saving a file with the same name as the zip archive minus the .zip extension. Ignored if --output does not end in ".zip".
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
import zipfile as zf

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

    output: str = args['--output']
    entry_ids: str = '\n'.join(entry_ids)

    if output is not None:
        if output.endswith('.zip'):
            u.save_to_zip_archive(zip_archive_path=output, zip_file_name=args['--zip-file'], file_content=entry_ids)
        else:
            with open(output, 'w') as file:
                file.write(entry_ids)
    else:
        print(entry_ids)
