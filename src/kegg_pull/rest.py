"""
KEGG REST API Operations
~~~~~~~~~~~~~~~~~~~~~~~~
Interface for the KEGG REST API including all its operations.

Usage:
    kegg_pull rest -h | --help
    kegg_pull rest info <database-name> [--output=<output>]
    kegg_pull rest list <database-name> [--output=<output>]
    kegg_pull rest get <entry-ids> [--entry-field=<entry-field>] [--output=<output>]
    kegg_pull rest find <database-name> <keywords> [--output=<output>]
    kegg_pull rest find <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>]
    kegg_pull rest conv <kegg-database-name> <outside-database-name> [--output=<output>]
    kegg_pull rest conv --conv-target=<target-database-name> <entry-ids> [--output=<output>]
    kegg_pull rest link <target-database-name> <source-database-name> [--output=<output>]
    kegg_pull rest link --link-target=<target-database-name> <entry-ids> [--output=<output>]
    kegg_pull rest ddi <drug-entry-ids> [--output=<output>]

Options:
    -h --help                               Show this help message.
    info                                    Executes the "info" KEGG API operation, getting information about a KEGG database.
    <database-name>                         The name of the database to get information about or entry IDs from.
    list                                    Executes the "list" KEGG API operation, getting the entry IDs of the provided database.
    --output=<output>                       The file to store the response body from the KEGG web API operation. Prints to the console if --output is not specified.
    get                                     Executes the "get" KEGG API operation, getting the entries of the provided entry IDs.
    <entry-ids>                             Comma separated list of entry IDs.
    --entry-field=<entry-field>             Optional field to extract from an entry instead of the default entry info (i.e. flat file or htext in the case of brite entries).
    find                                    Executes the "find" KEGG API operation, finding entry IDs based on provided queries.
    <keywords>                              Comma separated list of keywords to search entries with.
    --formula=<formula>                     Sequence of atoms in a chemical formula format to search for (e.g. "O5C7" searchers for molecule entries containing 5 oxygen atoms and/or 7 carbon atoms).
    --exact-mass=<exact-mass>               Either a single number (e.g. --exact-mass=155.5) or two numbers (e.g. --exact-mass=155.5 --exact-mass=244.4). If a single number, searches for molecule entries with an exact mass equal to that value rounded by the last decimal point. If two numbers, searches for molecule entries with an exact mass within the two values (a range).
    --molecular-weight=<molecular-weight>   Same as --exact-mass but searches based on the molecular weight.
    conv                                    Executes the "conv" KEGG API operation, converting entry IDs from an outside database to those of a KEGG database and vice versa.
    <kegg-database-name>                    The name of the KEGG database from which to view equivalent outside database entry IDs.
    <outside-database-name>                 The name of the non-KEGG database from which to view equivalent KEGG database entry IDs.
    --conv-target=<target-database-name>    The outside or KEGG database from which to view equivalent versions of the provided entry IDs. If a KEGG database, the provided entry IDs must be from an outside database and vice versa.
    link                                    Executes the "link" KEGG API operation, showing the IDs of entries that are connected/related to entries of other databases.
    <target-database-name>                  The name of the database to find cross-references in the source database.
    <source-database-name>                  The name of the database from which cross-references are found in the target database.
    --link-target-<target-database-name>    The name of the database to find cross-references in the provided entry IDs.
    ddi                                     Executes the "ddi" KEGG API operation, searching for drug to drug interactions. Providing one entry ID reports all known interactions, while providing multiple checks if any drug pair in a given set of drugs is CI or P. If providing multiple, all entries must belong to the same database.
    <drug-entry-ids>                        Comma separated list of drug entry IDs from the following databases: drug, ndc, or yj
"""
import enum as e
import requests as rq
import time as t
import inspect as ins
import logging as l
import docopt as d

from . import kegg_url as ku
from . import _utils as u


class KEGGresponse:
    class Status(e.Enum):
        SUCCESS = 1
        FAILED = 2
        TIMEOUT = 3

    def __init__(self, status: Status, kegg_url: ku.AbstractKEGGurl, text_body: str = None, binary_body: bytes = None):
        if status is None:
            raise ValueError('A status must be specified for the KEGG response')

        if status == KEGGresponse.Status.SUCCESS and (
            text_body is None or binary_body is None or text_body == '' or binary_body == b''
        ):
            raise ValueError('A KEGG response cannot be marked as successful if its response body is empty')

        self._status = status
        self._kegg_url = kegg_url
        self._text_body = text_body
        self._binary_body = binary_body

    @property
    def status(self) -> Status:
        return self._status

    @property
    def kegg_url(self) -> ku.AbstractKEGGurl:
        return self._kegg_url

    @property
    def text_body(self) -> str:
        return self._text_body

    @property
    def binary_body(self) -> bytes:
        return self._binary_body


class KEGGrest:
    def __init__(self, n_tries: int = 3, time_out: int = 60, sleep_time: float = 0.0):
        self._n_tries = n_tries if n_tries is not None else 3
        self._time_out = time_out if time_out is not None else 60
        self._sleep_time = sleep_time if time_out is not None else 0.0

        if self._n_tries < 1:
            raise ValueError(f'{self._n_tries} is not a valid number of tries to make a KEGG request.')

    def request(self, KEGGurl: type = None, kegg_url: ku.AbstractKEGGurl = None, **kwargs) -> KEGGresponse:
        kegg_url: ku.AbstractKEGGurl = KEGGrest._get_kegg_url(KEGGurl=KEGGurl, kegg_url=kegg_url, **kwargs)
        status = None

        for _ in range(self._n_tries):
            try:
                response: rq.Response = rq.get(url=kegg_url.url, timeout=self._time_out)

                if response.status_code == 200:
                    return KEGGresponse(
                        status=KEGGresponse.Status.SUCCESS, kegg_url=kegg_url, text_body=response.text,
                        binary_body=response.content
                    )
                else:
                    status = KEGGresponse.Status.FAILED
            except rq.exceptions.Timeout:
                status = KEGGresponse.Status.TIMEOUT
                t.sleep(self._sleep_time)

        return KEGGresponse(status=status, kegg_url=kegg_url)

    @staticmethod
    def _get_kegg_url(KEGGurl: type = None, kegg_url: ku.AbstractKEGGurl = None, **kwargs) -> ku.AbstractKEGGurl:
        if KEGGurl is None and kegg_url is None:
            raise ValueError(
                f'Either an instantiated kegg_url object must be provided or an extended class of '
                f'{ku.AbstractKEGGurl.__name__} along with the corresponding kwargs for its constructor.'
            )

        if kegg_url is not None and KEGGurl is not None:
            l.warning(
                'Both an instantiated kegg_url object and KEGGurl class are provided. Using the instantiated object...'
            )

        if kegg_url is not None:
            return kegg_url

        if ku.AbstractKEGGurl not in ins.getmro(KEGGurl):
            raise ValueError(
                f'The value for KEGGurl must be an inherited class of {ku.AbstractKEGGurl.__name__}. '
                f'The class "{KEGGurl.__name__}" is not.'
            )

        kegg_url: ku.AbstractKEGGurl = KEGGurl(**kwargs)

        return kegg_url

    def test(self, KEGGurl: type = None, kegg_url: ku.AbstractKEGGurl = None, **kwargs) -> bool:
        kegg_url: ku.AbstractKEGGurl = KEGGrest._get_kegg_url(KEGGurl=KEGGurl, kegg_url=kegg_url, **kwargs)

        for _ in range(self._n_tries):
            try:
                response: rq.Response = rq.head(url=kegg_url.url, timeout=self._time_out)

                if response.status_code == 200:
                    return True
            except rq.exceptions.Timeout:
                t.sleep(self._sleep_time)

        return False

    def list(self, database_name: str) -> KEGGresponse:
        return self.request(KEGGurl=ku.ListKEGGurl, database_name=database_name)

    def get(self, entry_ids: list, entry_field: str = None) -> KEGGresponse:
        return self.request(KEGGurl=ku.GetKEGGurl, entry_ids=entry_ids, entry_field=entry_field)

    def info(self, database_name: str) -> KEGGresponse:
        return self.request(KEGGurl=ku.InfoKEGGurl, database_name=database_name)

    def keywords_find(self, database_name: str, keywords: list) -> KEGGresponse:
        return self.request(KEGGurl=ku.KeywordsFindKEGGurl, database_name=database_name, keywords=keywords)

    def molecular_find(
        self, database_name: str, formula: str = None, exact_mass: float = None, molecular_weight: int = None
    ) -> KEGGresponse:
        return self.request(
            KEGGurl=ku.MolecularFindKEGGurl, database_name=database_name, formula=formula, exact_mass=exact_mass,
            molecular_weight=molecular_weight
        )

    def database_conv(self, kegg_database_name: str, outside_database_name: str) -> KEGGresponse:
        return self.request(
            KEGGurl=ku.DatabaseConvKEGGurl, kegg_database_name=kegg_database_name,
            outside_database_name=outside_database_name
        )

    def entries_conv(self, target_database_name: str, entry_ids: list) -> KEGGresponse:
        return self.request(
            KEGGurl=ku.EntriesConvKEGGurl, target_database_name=target_database_name, entry_ids=entry_ids
        )

    def database_link(self, target_database_name: str, source_database_name: str) -> KEGGresponse:
        return self.request(
            KEGGurl=ku.DatabaseLinkKEGGurl, target_database_name=target_database_name,
            source_database_name=source_database_name
        )

    def entries_link(self, target_database_name: str, entry_ids: list) -> KEGGresponse:
        return self.request(
            KEGGurl=ku.EntriesLinkKEGGurl, target_database_name=target_database_name, entry_ids=entry_ids
        )

    def ddi(self, drug_entry_ids: list) -> KEGGresponse:
        return self.request(KEGGurl=ku.DdiKEGGurl, drug_entry_ids=drug_entry_ids)


def main():
    args: dict = d.docopt(__doc__)
    database_name: str = args['<database-name>']
    entry_ids: str = args['<entry-ids>']
    output: str = args['--output']
    is_binary = False
    kegg_rest = KEGGrest()

    if args['info']:
        kegg_response: KEGGresponse = kegg_rest.info(database_name=database_name)
    elif args['list']:
        kegg_response: KEGGresponse = kegg_rest.list(database_name=database_name)
    elif args['get']:
        entry_ids: list = u.split_comma_separated_list(list_string=entry_ids)
        entry_field: str = args['--entry-field']

        if ku.GetKEGGurl.is_binary(entry_field=entry_field):
            is_binary = True

        kegg_response: KEGGresponse = kegg_rest.get(entry_ids=entry_ids, entry_field=entry_field)
    elif args['find']:
        if args['<keywords>']:
            keywords: list = u.split_comma_separated_list(list_string=args['<keywords>'])
            kegg_response: KEGGresponse = kegg_rest.keywords_find(database_name=database_name, keywords=keywords)
        else:
            formula, exact_mass, molecular_weight = u.get_molecular_attribute_args(args=args)

            kegg_response: KEGGresponse = kegg_rest.molecular_find(
                database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
            )
    elif args['conv']:
        if args['--conv-target']:
            target_database_name: str = args['--conv-target']
            entry_ids: list = u.split_comma_separated_list(list_string=entry_ids)

            kegg_response: KEGGresponse = kegg_rest.entries_conv(
                target_database_name=target_database_name, entry_ids=entry_ids
            )
        else:
            kegg_database_name = args['<kegg-database-name>']
            outside_database_name = args['<outside-database-name>']

            kegg_response: KEGGresponse = kegg_rest.database_conv(
                kegg_database_name=kegg_database_name, outside_database_name=outside_database_name
            )
    elif args['link']:
        if args['--link-target']:
            target_database_name: str = args['--link-target']
            entry_ids: list = u.split_comma_separated_list(list_string=entry_ids)

            kegg_response: KEGGresponse = kegg_rest.entries_link(
                target_database_name=target_database_name, entry_ids=entry_ids
            )
        else:
            target_database_name: str = args['<target-database-name>']
            source_database_name: str = args['<source-database-name>']

            kegg_response: KEGGresponse = kegg_rest.database_link(
                target_database_name=target_database_name, source_database_name=source_database_name
            )
    else:
        drug_entry_ids: str = args['<drug-entry-ids>']
        drug_entry_ids: list = u.split_comma_separated_list(list_string=drug_entry_ids)
        kegg_response: KEGGresponse = kegg_rest.ddi(drug_entry_ids=drug_entry_ids)

    if kegg_response.status == KEGGresponse.Status.FAILED:
        raise RuntimeError(
            f'The request to the KEGG web API failed with the following URL: {kegg_response.kegg_url.url}'
        )
    elif kegg_response.status == KEGGresponse.Status.TIMEOUT:
        raise RuntimeError(
            f'The request to the KEGG web API timed out with the following URL: {kegg_response.kegg_url.url}'
        )

    if is_binary:
        response_body: bytes = kegg_response.binary_body
        save_type: str = 'wb'
    else:
        response_body: str = kegg_response.text_body
        save_type: str = 'w'

    if output is None:
        if is_binary:
            l.warning('Printing binary response body')

        print(response_body)
    else:
        with open(output, save_type) as file:
            file.write(response_body)
