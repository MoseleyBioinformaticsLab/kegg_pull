"""
Usage:
    kegg_pull rest -h | --help
    kegg_pull rest list <database-name> [--output=<output>]
    kegg_pull rest get <entry-ids> [--entry-field=<entry-field>] [--output=<output>]
    kegg_pull rest find <database-name> <keywords> [--output=<output>]
    kegg_pull rest find <database-name> (--formula=<formula>|--exact-mass=<exact-mass>...|--molecular-weight=<molecular-weight>...) [--output=<output>]
    kegg_pull rest conv <kegg-database-name> <outside-database-name>
    kegg_pull rest conv --conv-target=<target-database-name> <entry-ids>
    kegg_pull rest link <target-database-name> <source-database-name>
    kegg_pull rest link --link-target=<target-database-name> <entry-ids>
    kegg_pull rest ddi <drug-entry-ids>

Options:
    list                                    Executes the "list" KEGG API operation, getting the entry IDs of the provided database.
    <database-name>                         The name of the database to get entry IDs from.
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
import docopt as d
import logging as l

from . import kegg_request as kr
from . import kegg_url as ku
from . import utils as u


class KEGGrest:
    def __init__(self, kegg_request: kr.KEGGrequest = None):
        self._kegg_request = kegg_request if kegg_request is not None else kr.KEGGrequest()

    def request(self, url_type: ku.UrlType, **kwargs) -> kr.KEGGresponse:
        kegg_url: ku.AbstractKEGGurl = ku.create_url(url_type=url_type, **kwargs)

        return self._kegg_request.execute_api_operation(kegg_url=kegg_url)

    def list(self, database_name: str) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.LIST, database_name=database_name)

    def get(self, entry_ids: list, entry_field: str = None) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.GET, entry_ids=entry_ids, entry_field=entry_field)

    def info(self, database_name: str) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.INFO, database_name=database_name)

    def keywords_find(self, database_name: str, keywords: list) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.KEYWORDS_FIND, database_name=database_name, keywords=keywords)

    def molecular_find(
        self, database_name: str, formula: str = None, exact_mass: float = None, molecular_weight: int = None
    ) -> kr.KEGGresponse:
        return self.request(
            url_type=ku.UrlType.MOLECULAR_FIND, database_name=database_name, formula=formula, exact_mass=exact_mass,
            molecular_weight=molecular_weight
        )

    def database_conv(self, kegg_database_name: str, outside_database_name: str) -> kr.KEGGresponse:
        return self.request(
            url_type=ku.UrlType.DATABASE_CONV, kegg_database_name=kegg_database_name,
            outside_database_name=outside_database_name
        )

    def entries_conv(self, target_database_name: str, entry_ids: list) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.ENTRIES_CONV, target_database_name=target_database_name, entry_ids=entry_ids)

    def database_link(self, target_database_name: str, source_database_name: str) -> kr.KEGGresponse:
        return self.request(
            url_type=ku.UrlType.DATABASE_LINK, target_database_name=target_database_name,
            source_database_name=source_database_name
        )

    def entries_link(self, target_database_name: str, entry_ids: list) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.ENTRIES_LINK, target_database_name=target_database_name, entry_ids=entry_ids)

    def ddi(self, drug_entry_ids: list) -> kr.KEGGresponse:
        return self.request(url_type=ku.UrlType.DDI, drug_entry_ids=drug_entry_ids)


def main():
    args: dict = d.docopt(__doc__)

    if args['--help']:
        print(__doc__)
        exit(0)

    database_name: str = args['<database-name>']
    entry_ids: str = args['<entry-ids>']
    output: str = args['--output']
    is_binary = False
    kegg_rest = KEGGrest()

    if args['list']:
        kegg_response: kr.KEGGresponse = kegg_rest.list(database_name=database_name)
    elif args['get']:
        entry_ids: list = u.split_comma_separated_list(list_string=entry_ids)
        entry_field: str = args['--entry-field']

        if ku.GetKEGGurl.is_binary(entry_field=entry_field):
            is_binary = True

        kegg_response: kr.KEGGresponse = kegg_rest.get(entry_ids=entry_ids, entry_field=entry_field)
    elif args['find']:
        if args['<keywords>']:
            keywords: list = u.split_comma_separated_list(list_string=args['<keywords>'])
            kegg_response: kr.KEGGresponse = kegg_rest.keywords_find(database_name=database_name, keywords=keywords)
        else:
            formula, exact_mass, molecular_weight = u.get_molecular_attribute_args(args=args)

            kegg_response: kr.KEGGresponse = kegg_rest.molecular_find(
                database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
            )
    elif args['conv']:
        if args['--conv-target']:
            target_database_name: str = args['--conv-target']
            entry_ids: list = u.split_comma_separated_list(list_string=entry_ids)

            kegg_response: kr.KEGGresponse = kegg_rest.entries_conv(
                target_database_name=target_database_name, entry_ids=entry_ids
            )
        else:
            kegg_database_name = args['<kegg-database-name>']
            outside_database_name = args['<outside-database-name>']

            kegg_response: kr.KEGGresponse = kegg_rest.database_conv(
                kegg_database_name=kegg_database_name, outside_database_name=outside_database_name
            )
    elif args['link']:
        if args['--link-target']:
            target_database_name: str = args['--link-target']
            entry_ids: list = u.split_comma_separated_list(list_string=entry_ids)

            kegg_response: kr.KEGGresponse = kegg_rest.entries_link(
                target_database_name=target_database_name, entry_ids=entry_ids
            )
        else:
            target_database_name: str = args['<target-database-name>']
            source_database_name: str = args['<source-database-name>']

            kegg_response: kr.KEGGresponse = kegg_rest.database_link(
                target_database_name=target_database_name, source_database_name=source_database_name
            )
    else:
        drug_entry_ids: str = args['<drug-entry-ids']
        drug_entry_ids: list = u.split_comma_separated_list(list_string=drug_entry_ids)
        kegg_response: kr.KEGGresponse = kegg_rest.ddi(drug_entry_ids=drug_entry_ids)

    if kegg_response.status == kr.KEGGresponse.Status.FAILED:
        raise RuntimeError(
            f'The request to the KEGG web API failed with the following URL: {kegg_response.kegg_url.url}'
        )
    elif kegg_response.status == kr.KEGGresponse.Status.TIMEOUT:
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
