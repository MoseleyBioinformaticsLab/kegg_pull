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
