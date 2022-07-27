import requests as rq
import enum as e
import time as t
import logging as l


class WebResponse:
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
            raise ValueError('A status must be specified for the web response')

        if status == WebResponse.Status.SUCCESS and (
            text_body is None or binary_body is None or text_body == '' or binary_body == b''
        ):
            raise ValueError('A web response cannot be marked as successful if its response body is empty')


class WebRequest:
    def __init__(self, n_tries: int = 3, time_out: int = 60, sleep_time: float = 0.0):
        self._n_tries = n_tries if n_tries is not None else 3
        self._time_out = time_out if time_out is not None else 60
        self._sleep_time = sleep_time if time_out is not None else 0.0
        self._validate()

    def _validate(self):
        if self._n_tries < 1:
            l.warning(f'{self._n_tries} is not a valid number of tries to make a web request. Doing 1 try')
            self._n_tries = 1

    def get(self, url: str):
        status = None

        for _ in range(self._n_tries):
            try:
                res: rq.Response = rq.get(url=url, timeout=self._time_out)

                if res.status_code == 200:
                    return WebResponse(status=WebResponse.Status.SUCCESS, text_body=res.text, binary_body=res.content)
                else:
                    status = WebResponse.Status.FAILED
            except rq.exceptions.Timeout:
                status = WebResponse.Status.TIMEOUT
                t.sleep(self._sleep_time)

        return WebResponse(status=status)
