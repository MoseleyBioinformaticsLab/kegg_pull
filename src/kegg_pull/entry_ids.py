"""
Usage:
    kegg_pull entry-ids -h | --help
    kegg_pull entry-ids from-database <database-name> [--output=<output>]
    kegg_pull entry-ids from-file <file-path> [--output=<output>]
    kegg_pull entry-ids from-keywords <database-name> <keywords> [--output=<output>]
    kegg_pull entry-ids from-molecular-attribute <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>]

Options:
    -h --help                               Show this help message.
    from-database                           Gets all the entry IDs within a given database.
    <database-name>                         The KEGG database from which to get a list of entry IDs.
    --output=<output>                       Path to the file to store the output (1 entry ID per line). Prints to the console if not specified.
    from-file                               Loads the entry IDs from a file.
    <file-path>                             Path to a file containing a list of entry IDs with one entry ID on each line.
    from-keywords                           Searches for entries within a database based on provided keywords.
    <keywords>                              Comma separated list of keywords to search within entries (e.g. --keywords=kw1,k2w,kw3 etc.).
    from-molecular-attribute                Searches a database of molecule-type KEGG entries by molecular attributes.
    --formula=<formula>                     Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searchers for molecule entries containing 5 oxygen atoms and/or 7 carbon atoms).
    --exact-mass=<exact-mass>               Either a single number (e.g. --exact-mass=155.5) or two numbers (e.g. --exact-mass=155.5 --exact-mass=244.4). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
    --molecular-weight=<molecular-weight>   Same as --exact-mass but searches based on the molecular weight.
"""
import typing as t
import docopt as d

from . import kegg_request as kr
from . import rest as r
from . import utils as u


class EntryIdsGetter:
    def __init__(self, kegg_request: kr.KEGGrequest = None):
        self._kegg_rest = r.KEGGrest(kegg_request=kegg_request)

    def from_database(self, database_name: str) -> list:
        kegg_response: kr.KEGGresponse = self._kegg_rest.list(database_name=database_name)

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


    @staticmethod
    def _process_response(kegg_response: kr.KEGGresponse) -> list:
        if kegg_response.status == kr.KEGGresponse.Status.FAILED:
            raise RuntimeError(
                f'The KEGG request failed to get the entry IDs from the following URL: {kegg_response.kegg_url.url}'
            )
        elif kegg_response.status == kr.KEGGresponse.Status.TIMEOUT:
            raise RuntimeError(
                f'The KEGG request timed out while trying to get the entry IDs from the following URL: '
                f'{kegg_response.kegg_url.url}'
            )

        entry_ids: list = EntryIdsGetter._parse_entry_ids_string(entry_ids_string=kegg_response.text_body)

        return entry_ids


    @staticmethod
    def from_file(file_path: str) -> list:
        with open(file_path, 'r') as f:
            entry_ids: str = f.read()

            if entry_ids == '':
                raise ValueError(f'Attempted to get entry IDs from {file_path}. But the file is empty')

            entry_ids: list = EntryIdsGetter._parse_entry_ids_string()

        return entry_ids


    @staticmethod
    def _parse_entry_ids_string(entry_ids_string: str) -> list:
        entry_ids: list = entry_ids_string.strip().split('\n')
        entry_ids = [entry_id.split('\t')[0].strip() for entry_id in entry_ids]

        return entry_ids


    def from_keywords(self, database_name: str, keywords: list) -> list:
        kegg_response: kr.KEGGresponse = self._kegg_rest.keywords_find(database_name=database_name, keywords=keywords)

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


    def from_molecular_attribute(
        self, database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
        molecular_weight: t.Union[int, tuple] = None
    ) -> list:
        kegg_response: kr.KEGGresponse = self._kegg_rest.molecular_find(
            database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
        )

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


def main():
    args: dict = d.docopt(__doc__)

    if args['--help']:
        print(__doc__)
        exit(0)

    database_name: str = args['<database-name>']
    entry_ids_getter = EntryIdsGetter()

    if args['from-database']:
        entry_ids: list = entry_ids_getter.from_database(database_name=database_name)
    elif args['from-file']:
        entry_ids_file_path: str = args['<file-path>']
        entry_ids: list = EntryIdsGetter.from_file(file_path=entry_ids_file_path)
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

    if output is not None:
        with open(output, 'w') as f:
            for entry_id in entry_ids:
                f.write(entry_id + '\n')
    else:
        for entry_id in entry_ids:
            print(entry_id)
