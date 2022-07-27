from . import web_request as wr


class PullResult:
    def __init__(self):
        self._successful_entry_ids = []
        self._failed_entry_ids = []
        self._timed_out_entry_ids = []

    @property
    def successful_entry_ids(self):
        return tuple(self._successful_entry_ids)

    @property
    def failed_entry_ids(self):
        return tuple(self._failed_entry_ids)

    @property
    def timed_out_entry_ids(self):
        return tuple(self._timed_out_entry_ids)

    def add_entry_ids(self, *entry_ids, status: wr.WebResponse.Status):
        if status == wr.WebResponse.Status.SUCCESS:
            self._successful_entry_ids.extend(entry_ids)
        elif status == wr.WebResponse.Status.FAILED:
            self._failed_entry_ids.extend(entry_ids)
        elif status == wr.WebResponse.Status.TIMEOUT:
            self._timed_out_entry_ids.extend(entry_ids)

    def merge_pull_results(self, other):
        self._successful_entry_ids.extend(other.successful_entry_ids)
        self._failed_entry_ids.extend(other.failed_entry_ids)
        self._timed_out_entry_ids.extend(other.timed_out_entry_ids)
