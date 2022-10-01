"""
KEGG REST API Operations
~~~~~~~~~~~~~~~~~~~~~~~~
Interface for the KEGG REST API including all its operations.
"""
import enum as e
import requests as rq
import time as t
import inspect as ins
import logging as l

from . import kegg_url as ku


class KEGGresponse:
    """Class containing details of a response from the KEGG REST API."""

    class Status(e.Enum):
        """The status of a KEGG response."""
        SUCCESS = 1
        FAILED = 2
        TIMEOUT = 3

    def __init__(self, status: Status, kegg_url: ku.AbstractKEGGurl, text_body: str = None, binary_body: bytes = None) -> None:
        """
        :param status: The status of the KEGG response.
        :param kegg_url: The URL used in the request to the KEGG REST API that resulted in the KEGG response.
        :param text_body: The text version of the response body.
        :param binary_body: The binary version of the response body.
        :raises ValueError: Raised if the status is SUCCESS but a response body is not provided.
        """
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
    """Class containing methods for making requests to the KEGG REST API, including all the KEGG REST API operations."""

    def __init__(self, n_tries: int = 3, time_out: int = 60, sleep_time: float = 10.0):
        """
        :param n_tries: The number of times to try to make a request (can succeed the first time, or any of n_tries, or none of the tries).
        :param time_out: The number of seconds to wait for a request until marking it as timed out.
        :param sleep_time: The number of seconds to wait in between timed out requests or blacklisted requests.
        """
        self._n_tries = n_tries if n_tries is not None else 3
        self._time_out = time_out if time_out is not None else 60
        self._sleep_time = sleep_time if sleep_time is not None else 10.0

        if self._n_tries < 1:
            raise ValueError(f'{self._n_tries} is not a valid number of tries to make a KEGG request.')

    def request(self, KEGGurl: type = None, kegg_url: ku.AbstractKEGGurl = None, **kwargs) -> KEGGresponse:
        """ General KEGG request function based on a given KEGG URL (either a class that is instantiated or an already instantiated KEGG URL object).

        :param KEGGurl: Optional KEGG URL class (extended from AbstractKEGGurl) that's instantiated with provided keyword arguments.
        :param kegg_url: Optional KEGGurl object that's already instantiated (used if KEGGurl class is not provided).
        :param kwargs: The keyword arguments used to instantiate the KEGGurl class, if provided.
        :return: The KEGG response.
        """
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

                if response.status_code == 403:
                    # 403 forbidden. KEGG may have blocked the request due to too many requests in too little time.
                    # In case blacklisting, sleep to allow time for KEGG to unblock further requests.
                    t.sleep(self._sleep_time)
            except rq.exceptions.Timeout:
                status = KEGGresponse.Status.TIMEOUT
                t.sleep(self._sleep_time)

        return KEGGresponse(status=status, kegg_url=kegg_url)

    @staticmethod
    def _get_kegg_url(KEGGurl: type = None, kegg_url: ku.AbstractKEGGurl = None, **kwargs) -> ku.AbstractKEGGurl:
        """ Gets the KEGGurl object to be used to make the request to KEGG.

        :param KEGGurl: Optional KEGGurl class to instantiate a KEGGurl object using keyword arguments.
        :param kegg_url: Instantiated KEGGurl object that's simply returned if provided (used if the KEGGurl class is not provided).
        :param kwargs: The keyword arguments used to instantiate the KEGGurl object if a KEGGurl class is provided.
        :return: The KEGGurl object.
        :raises ValueError: Raised if both a class and object are provided or the class does not inherit from AbstractKEGGurl.
        """
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
        """ Tests if a KEGGurl will succeed upon being used in a request to the KEGG REST API.

        :param KEGGurl: Optional KEGGurl class used to instantiate a KEGGurl object given keyword arguments.
        :param kegg_url: KEGGurl object that's already instantiated (used if a KEGGurl class is not provided).
        :param kwargs: The keyword arguments used to instantiated the KEGGurl object from the KEGGurl class, if provided.
        :return: True if the URL would succeed, false if it would fail or time out.
        """
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
        """ Executes the "list" KEGG API operation, pulling the entry IDs of the provided database.

        :param database_name: The database from which to pull entry IDs.
        :return: The KEGG response.
        """
        return self.request(KEGGurl=ku.ListKEGGurl, database_name=database_name)

    def get(self, entry_ids: list, entry_field: str = None) -> KEGGresponse:
        """ Executes the "get" KEGG API operation, pulling the entries of the provided entry IDs.

        :param entry_ids: The IDs of entries to pull.
        :param entry_field: Optional field to extract from the entries.
        :return: The KEGG response.
        """
        return self.request(KEGGurl=ku.GetKEGGurl, entry_ids=entry_ids, entry_field=entry_field)

    def info(self, database_name: str) -> KEGGresponse:
        """ Executes the "info" KEGG API operation, pulling information about a KEGG database.

        :param database_name: The database to pull information about.
        :return: The KEGG response
        """
        return self.request(KEGGurl=ku.InfoKEGGurl, database_name=database_name)

    def keywords_find(self, database_name: str, keywords: list) -> KEGGresponse:
        """ Executes the "find" KEGG API operation, finding entry IDs based on keywords to search in entries.

        :param database_name: The name of the database containing entries to search for.
        :param keywords: The keywords to search in entries.
        :return: The KEGG response
        """
        return self.request(KEGGurl=ku.KeywordsFindKEGGurl, database_name=database_name, keywords=keywords)

    def molecular_find(
        self, database_name: str, formula: str = None, exact_mass: float = None, molecular_weight: int = None
    ) -> KEGGresponse:
        """ Executes the "find" KEGG API operation, finding entry IDs in chemical databases based on one (and only one) choice of three molecular attributes of the entries.

        :param database_name: The name of the chemical database to search for entries in.
        :param formula: The chemical formula (one of three choices) of chemical entries to search for.
        :param exact_mass: The exact mass (one of three choices) of chemical entries to search for (single value or range).
        :param molecular_weight: The molecular weight (one of three choices) of chemical entries to search for (single value or range).
        :return: The KEGG response
        """
        return self.request(
            KEGGurl=ku.MolecularFindKEGGurl, database_name=database_name, formula=formula, exact_mass=exact_mass,
            molecular_weight=molecular_weight
        )

    def database_conv(self, kegg_database_name: str, outside_database_name: str) -> KEGGresponse:
        """ Executes the "conv" KEGG API operation, converting the entry IDs of a KEGG database to those of an outside database.

        :param kegg_database_name: The name of the KEGG database to pull converted entry IDs from.
        :param outside_database_name: The name of the outside database to pull converted entry IDs from.
        :return: The KEGG response.
        """
        return self.request(
            KEGGurl=ku.DatabaseConvKEGGurl, kegg_database_name=kegg_database_name,
            outside_database_name=outside_database_name
        )

    def entries_conv(self, target_database_name: str, entry_ids: list) -> KEGGresponse:
        """ Executes the "conv" KEGG API operation, converting provided entry IDs from one database to the form of a target database.

        :param target_database_name: The name of the database to get converted entry IDs from.
        :param entry_ids: The entry IDs to convert to the form of the target database.
        :return: The KEGG response.
        """
        return self.request(
            KEGGurl=ku.EntriesConvKEGGurl, target_database_name=target_database_name, entry_ids=entry_ids
        )

    def database_link(self, target_database_name: str, source_database_name: str) -> KEGGresponse:
        """ Executes the "link" KEGG API operation, showing the IDs of entries in one KEGG database that are connected/related to entries of another KEGG database.

        :param target_database_name: One of the two KEGG databases to pull linked entries from.
        :param source_database_name: The other KEGG database to link entries from the target database.
        :return: The KEGG response
        """
        return self.request(
            KEGGurl=ku.DatabaseLinkKEGGurl, target_database_name=target_database_name,
            source_database_name=source_database_name
        )

    def entries_link(self, target_database_name: str, entry_ids: list) -> KEGGresponse:
        """ Executes the "link" KEGG API operation, showing the IDs of entries that are connected/related to entries of a provided databases.

        :param target_database_name: The KEGG database to find links to the provided entries.
        :param entry_ids: The IDs of the entries to link to entries in the target database.
        :return: The KEGG response
        """
        return self.request(
            KEGGurl=ku.EntriesLinkKEGGurl, target_database_name=target_database_name, entry_ids=entry_ids
        )

    def ddi(self, drug_entry_ids: list) -> KEGGresponse:
        """ Executes the "ddi" KEGG API operation, searching for drug to drug interactions. Providing one entry ID reports all known interactions, while providing multiple checks if any drug pair in a given set of drugs is CI or P. If providing multiple, all entries must belong to the same database.

        :param drug_entry_ids: The IDs of the drug entries within which search for drug interactions.
        :return: The KEGG response
        """
        return self.request(KEGGurl=ku.DdiKEGGurl, drug_entry_ids=drug_entry_ids)
