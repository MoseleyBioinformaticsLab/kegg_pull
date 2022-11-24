"""
Usage:
    kegg_pull entry-ids -h | --help
    kegg_pull entry-ids database <database-name> [--output=<output>]
    kegg_pull entry-ids keywords <database-name> <keywords> [--output=<output>]
    kegg_pull entry-ids molecular-attribute <database-name> (--formula=<formula>|--em=<exact-mass>...|--mw=<molecular-weight>...) [--output=<output>]

Options:
    -h --help               Show this help message.
    database                Pulls all the entry IDs within a given database.
    <database-name>         The KEGG database from which to pull a list of entry IDs.
    --output=<output>       Path to the file (either in a directory or ZIP archive) to store the output (1 entry ID per line). Prints to the console if not specified. If a ZIP archive, the file path must be in the form of /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:file.txt).
    keywords                Searches for entries within a database based on provided keywords.
    <keywords>              Comma separated list of keywords to search entries with (e.g. kw1,kw2,kw3 etc.). Or if equal to "-", keywords are read from standard input, one keyword per line; Press CTRL+D to finalize input or pipe (e.g. cat file.txt | kegg_pull rest find brite - ...).
    molecular-attribute     Searches a database of molecule-type KEGG entries by molecular attributes.
    --formula=<formula>     Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searches for molecule entries containing 5 oxygen atoms and/or 7 carbon atoms).
    --em=<exact-mass>       Either a single number (e.g. "--em=155.5") or two numbers (e.g. "--em=155.5 --em=244.4"). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
    --mw=<molecular-weight> Same as "--em=<exact-mass>" but searches based on the molecular weight.
"""
import docopt as d

from . import entry_ids as ei
from . import _utils as u


def main():
    args: dict = d.docopt(__doc__)
    database_name: str = args['<database-name>']

    if args['database']:
        entry_ids: list = ei.from_database(database_name=database_name)
    elif args['keywords']:
        keywords: list = u.handle_cli_input(input_source=args['<keywords>'])
        entry_ids: list = ei.from_keywords(database_name=database_name, keywords=keywords)
    else:
        formula, exact_mass, molecular_weight = u.get_molecular_attribute_args(args=args)

        entry_ids: list = ei.from_molecular_attribute(
            database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
        )

    entry_ids: str = '\n'.join(entry_ids)
    u.handle_cli_output(output_target=args['--output'], output_content=entry_ids)
