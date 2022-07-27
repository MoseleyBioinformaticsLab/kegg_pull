import multiprocessing as mp
import os
import abc
import typing as t
import pickle as p

from . import single_pull as sp
from . import kegg_url as ku
from . import pull_result as pr


class MultiplePull(abc.ABC):
    def __init__(self, single_pull: sp.SinglePull, force_single_entry: bool = False):
        self._single_pull = single_pull
        self._force_single_entry = force_single_entry

    def pull(
        self, entry_ids: list, entry_field: t.Optional[str] = '', force_single_entry: t.Optional[bool] = None
    ) -> pr.PullResult:
        force_single_entry = force_single_entry if force_single_entry is not None else self._force_single_entry

        # If a new entry field is provided, update it
        if entry_field != '':
            self._single_pull.entry_field = entry_field

        entry_ids: list = self._group_entry_ids(
            entry_ids_to_group=entry_ids, force_single_entry=force_single_entry
        )

        return self._pull(grouped_entry_ids=entry_ids)

    def _group_entry_ids(self, entry_ids_to_group: list, force_single_entry: bool) -> list:
        group_size: int = MultiplePull._get_n_entries_per_url(
            force_single_entry=force_single_entry, entry_field=self._single_pull.entry_field
        )

        grouped_entry_ids = []

        for i in range(0, len(entry_ids_to_group), group_size):
            entry_id_group: list = entry_ids_to_group[i:i + group_size]
            grouped_entry_ids.append(entry_id_group)

        return grouped_entry_ids

    @staticmethod
    def _get_n_entries_per_url(force_single_entry: bool, entry_field: str) -> int:
        if force_single_entry:
            return 1
        elif ku.GetKEGGurl.only_one_entry(entry_field=entry_field):
            return 1
        else:
            return ku.GetKEGGurl.MAX_ENTRY_IDS_PER_URL

    @abc.abstractmethod
    def _pull(self, grouped_entry_ids: list):
        pass

class SingleProcessMultiplePull(MultiplePull):
    def _pull(self, grouped_entry_ids: list):
        multiple_pull_result = pr.PullResult()

        for entry_id_group in grouped_entry_ids:
            single_pull_result: pr.PullResult = self._single_pull.pull(entry_ids=entry_id_group)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result

class MultiProcessMultiplePull(MultiplePull):
    def __init__(self, single_pull: sp.SinglePull, force_single_entry: bool = False, n_workers: int = os.cpu_count()):
        super(MultiProcessMultiplePull, self).__init__(single_pull=single_pull, force_single_entry=force_single_entry)
        self._n_workers = n_workers

    def _pull(self, grouped_entry_ids: list):
        multiple_pull_result = pr.PullResult()
        args = [(entry_ids, self._single_pull) for entry_ids in grouped_entry_ids]
        chunk_size: int = len(grouped_entry_ids) // self._n_workers

        with mp.Pool(self._n_workers) as pool:
            results: list = pool.starmap(_get_single_pull_result, args, chunksize=chunk_size)

        for result in results:
            single_pull_result: pr.PullResult = p.loads(result)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result

def _get_single_pull_result(entry_ids: list, single_pull: sp.SinglePull) -> bytes:
    single_pull_result: pr.PullResult = single_pull.pull(entry_ids=entry_ids)

    return p.dumps(single_pull_result)
