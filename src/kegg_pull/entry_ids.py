"""
Pulling Lists of KEGG Entry IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for pulling lists of KEGG entry IDs from the KEGG REST API.
"""
import typing as t

from . import rest as r


class EntryIdsGetter:
    """
    Class with methods for various ways of pulling a list of KEGG entry IDs from the KEGG REST API.
    """

    def __init__(self, kegg_rest: r.KEGGrest = None) -> None:
        """
        :param kegg_rest: Optional KEGGrest object for making requests to the KEGG REST API to pull entry IDs (if a KEGGrest object is not provided, a KEGGrest object is created with the default values).
        """
        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()

    def from_database(self, database_name: str) -> list:
        """ Pulls the KEGG entry IDs of a given database.

        :param database_name: The KEGG database to pull the entry IDs from.
        :return: The list of resulting entry IDs.
        :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.list(database_name=database_name)

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


    @staticmethod
    def _process_response(kegg_response: r.KEGGresponse) -> list:
        """ Extracts the entry IDs from a KEGG response if successful, else raises an exception.

        :param kegg_response: The response from the KEGG REST API containing entry IDs if successful.
        :return: The list of KEGG entry IDs.
        :raises RuntimeError: Raised if the KEGG response indicates a failure or time out.
        """
        if kegg_response.status == r.KEGGresponse.Status.FAILED:
            raise RuntimeError(
                f'The KEGG request failed to pull the entry IDs from the following URL: {kegg_response.kegg_url.url}'
            )
        elif kegg_response.status == r.KEGGresponse.Status.TIMEOUT:
            raise RuntimeError(
                f'The KEGG request timed out while trying to pull the entry IDs from the following URL: '
                f'{kegg_response.kegg_url.url}'
            )

        entry_ids: list = EntryIdsGetter._parse_entry_ids_string(entry_ids_string=kegg_response.text_body)

        return entry_ids


    @staticmethod
    def from_file(file_path: str) -> list:
        """ Loads KEGG entry IDs that are listed in a file with one entry ID on each line.

        :param file_path: The path to the file containing the entry IDs.
        :return: The list of entry IDs.
        :raises ValueError: Raised if the file is empty.
        """
        with open(file_path, 'r') as file:
            entry_ids: str = file.read()

            if entry_ids == '':
                raise ValueError(f'Attempted to load entry IDs from {file_path}. But the file is empty')

            entry_ids: list = EntryIdsGetter._parse_entry_ids_string(entry_ids_string=entry_ids)

        return entry_ids


    @staticmethod
    def _parse_entry_ids_string(entry_ids_string: str) -> list:
        """ Parses the entry IDs contained in a string.

        :param entry_ids_string: The string containing the entry IDs.
        :return: The list of parsed entry IDs.
        """
        entry_ids: list = entry_ids_string.strip().split('\n')
        entry_ids = [entry_id.split('\t')[0].strip() for entry_id in entry_ids]

        return entry_ids


    def from_keywords(self, database_name: str, keywords: list) -> list:
        """ Pulls entry IDs from a database based on keywords searched in the entries.

        :param database_name: The name of the database to pull entry IDs from.
        :param keywords: The keywords to search entries in the database with.
        :return: The list of entry IDs.
        :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.keywords_find(database_name=database_name, keywords=keywords)

        return EntryIdsGetter._process_response(kegg_response=kegg_response)


    def from_molecular_attribute(
        self, database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
        molecular_weight: t.Union[int, tuple] = None
    ) -> list:
        """ Pulls entry IDs from a database containing chemical entries based on one (and only one) of three molecular attributes of the entries.

        :param database_name: The name of the database containing chemical entries.
        :param formula: The chemical formula to search for.
        :param exact_mass: The exact mass of the compound to search for (a single value or a range).
        :param molecular_weight: The molecular weight of the compound to search for (a single value or a range).
        :return: The list of entry IDs.
        :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.molecular_find(
            database_name=database_name, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight
        )

        return EntryIdsGetter._process_response(kegg_response=kegg_response)
