import requests as rq
import enum as e
import time as t

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
    def status(self):
        return self._status

    @property
    def kegg_url(self):
        return self._kegg_url

    @property
    def text_body(self):
        return self._text_body

    @property
    def binary_body(self):
        return self._binary_body


class KEGGrequest:
    def __init__(self, n_tries: int = 3, time_out: int = 60, sleep_time: float = 0.0):
        self._n_tries = n_tries if n_tries is not None else 3
        self._time_out = time_out if time_out is not None else 60
        self._sleep_time = sleep_time if time_out is not None else 0.0

        if self._n_tries < 1:
            raise ValueError(f'{self._n_tries} is not a valid number of tries to make a KEGG request.')

    def execute_api_operation(self, kegg_url: ku.AbstractKEGGurl) -> KEGGresponse:
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

    def test(self, url: str) -> bool:
        for _ in self._n_tries:
            try:
                response: rq.Response = rq.head(url=url, timeout=self._time_out)

                if response.status_code == 200:
                    return True
            except rq.exceptions.Timeout:
                t.sleep(self._sleep_time)

        return False
