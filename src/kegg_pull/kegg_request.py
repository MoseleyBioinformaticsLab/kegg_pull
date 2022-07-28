import requests as rq
import enum as e
import time as t


class KEGGresponse:
    class Status(e.Enum):
        SUCCESS = 1
        FAILED = 2
        TIMEOUT = 3

    def __init__(self, status: Status, text_body: str = None, binary_body: bytes = None):
        self._validate(status=status, text_body=text_body, binary_body=binary_body)
        self._status = status
        self._text_body = text_body
        self._binary_body = binary_body

    @property
    def status(self):
        return self._status

    @property
    def text_body(self):
        return self._text_body

    @property
    def binary_body(self):
        return self._binary_body

    @staticmethod
    def _validate(status: Status, text_body: str, binary_body: bytes):
        if status is None:
            raise ValueError('A status must be specified for the KEGG response')

        if status == KEGGresponse.Status.SUCCESS and (
            text_body is None or binary_body is None or text_body == '' or binary_body == b''
        ):
            raise ValueError('A KEGG response cannot be marked as successful if its response body is empty')


class KEGGrequest:
    def __init__(self, n_tries: int = 3, time_out: int = 60, sleep_time: float = 0.0):
        self._n_tries = n_tries if n_tries is not None else 3
        self._time_out = time_out if time_out is not None else 60
        self._sleep_time = sleep_time if time_out is not None else 0.0

        if self._n_tries < 1:
            raise ValueError(f'{self._n_tries} is not a valid number of tries to make a KEGG request.')

    def get(self, url: str):
        status = None

        for _ in range(self._n_tries):
            try:
                response: rq.Response = rq.get(url=url, timeout=self._time_out)

                if response.status_code == 200:
                    return KEGGresponse(status=KEGGresponse.Status.SUCCESS, text_body=response.text, binary_body=response.content)
                else:
                    status = KEGGresponse.Status.FAILED
            except rq.exceptions.Timeout:
                status = KEGGresponse.Status.TIMEOUT
                t.sleep(self._sleep_time)

        return KEGGresponse(status=status)

    def test(self, url: str) -> bool:
        for _ in self._n_tries:
            try:
                response: rq.Response = rq.head(url=url, timeout=self._time_out)

                if response.status_code == 200:
                    return True
            except rq.exceptions.Timeout:
                t.sleep(self._sleep_time)

        return False
