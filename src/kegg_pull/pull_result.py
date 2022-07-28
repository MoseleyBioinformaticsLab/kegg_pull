from . import kegg_request as kr


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

    def add_entry_ids(self, *entry_ids, status: kr.KEGGresponse.Status):
        if status == kr.KEGGresponse.Status.SUCCESS:
            self._successful_entry_ids.extend(entry_ids)
        elif status == kr.KEGGresponse.Status.FAILED:
            self._failed_entry_ids.extend(entry_ids)
        elif status == kr.KEGGresponse.Status.TIMEOUT:
            self._timed_out_entry_ids.extend(entry_ids)

    def merge_pull_results(self, other):
        self._successful_entry_ids.extend(other.successful_entry_ids)
        self._failed_entry_ids.extend(other.failed_entry_ids)
        self._timed_out_entry_ids.extend(other.timed_out_entry_ids)
