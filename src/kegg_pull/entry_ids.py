"""
Getting Lists of KEGG Entry IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for getting lists of KEGG entry IDs from the KEGG REST API.
"""
import typing as t

from . import rest as r


class EntryIdsGetter:
    """
    Class with methods for various ways of getting a list of KEGG entry IDs from the KEGG REST API.
    """
    def __init__(self, kegg_rest: r.KEGGrest = None):
        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()

    def from_database(self, database_name: str) -> list:
        kegg_response: r.KEGGresponse = self._kegg_rest.list(database_name=database_name)

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


    @staticmethod
    def _process_response(kegg_response: r.KEGGresponse) -> list:
        if kegg_response.status == r.KEGGresponse.Status.FAILED:
            raise RuntimeError(
                f'The KEGG request failed to get the entry IDs from the following URL: {kegg_response.kegg_url.url}'
            )
        elif kegg_response.status == r.KEGGresponse.Status.TIMEOUT:
            raise RuntimeError(
                f'The KEGG request timed out while trying to get the entry IDs from the following URL: '
                f'{kegg_response.kegg_url.url}'
            )

        entry_ids: list = EntryIdsGetter._parse_entry_ids_string(entry_ids_string=kegg_response.text_body)

        return entry_ids


    @staticmethod
    def from_file(file_path: str) -> list:
        with open(file_path, 'r') as file:
            entry_ids: str = file.read()

            if entry_ids == '':
                raise ValueError(f'Attempted to get entry IDs from {file_path}. But the file is empty')

            entry_ids: list = EntryIdsGetter._parse_entry_ids_string(entry_ids_string=entry_ids)

        return entry_ids


    @staticmethod
    def _parse_entry_ids_string(entry_ids_string: str) -> list:
        entry_ids: list = entry_ids_string.strip().split('\n')
        entry_ids = [entry_id.split('\t')[0].strip() for entry_id in entry_ids]

        return entry_ids


    def from_keywords(self, database_name: str, keywords: list) -> list:
        kegg_response: r.KEGGresponse = self._kegg_rest.keywords_find(database_name=database_name, keywords=keywords)

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


    def from_molecular_attribute(
        self, database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
        molecular_weight: t.Union[int, tuple] = None
    ) -> list:
        kegg_response: r.KEGGresponse = self._kegg_rest.molecular_find(
            database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
        )

        return EntryIdsGetter._process_response(kegg_response=kegg_response)
