import multiprocessing as mp
import os
import typing as t
import requests as rq

import src.kegg_pull.kegg_url as ku
import src.kegg_pull.make_urls_from_entry_id_list as mu
import src.kegg_pull.single_pull as sp
import src.kegg_pull.separate_entries as se


def multiple_pull(
    output_dir: str, database_type: str = None, entry_id_list_path: str = None, entry_field: str = None,
    n_workers: int = os.cpu_count()
):
    get_urls: list = mu.make_urls_from_entry_id_list(
        database_type=database_type, entry_id_list_path=entry_id_list_path, entry_field=entry_field
    )

    kegg_puller = _MultiThreadedKEGGpuller(
        urls_to_pull=get_urls, output_dir=output_dir, n_workers=n_workers, entry_field=entry_field
    )

    return kegg_puller.pull()


class _MultiThreadedKEGGpuller:
    def __init__(self, urls_to_pull: list, output_dir: str, n_workers: int, entry_field: str):
        self._urls_remaining = urls_to_pull
        self._output_dir = output_dir
        self._n_workers = n_workers
        self._entry_field = entry_field
        self._failed_entry_ids = []
        self._successful_entry_ids = []
        self._timed_out_urls = []

    def pull(self) -> tuple:
        if not os.path.isdir(self._output_dir):
            os.mkdir(self._output_dir)

        all_successful_entry_ids = []
        all_failed_entry_ids = []

        while len(self._urls_remaining) > 0:
            chunk_size: int = len(self._urls_remaining) // self._n_workers

            if chunk_size == 0:
                chunk_size = 1

            with mp.Pool(self._n_workers) as p:
                results: list = p.map(self._pull_and_save, self._urls_remaining, chunksize=chunk_size)

            for successful_entry_ids, failed_entry_ids in results:
                all_successful_entry_ids.extend(successful_entry_ids)
                all_failed_entry_ids.extend(all_failed_entry_ids)

            self._urls_remaining = self._timed_out_urls

        return all_successful_entry_ids, all_failed_entry_ids

    def _pull_and_save(self, get_url: ku.GetKEGGurl):
        try:
            res: Response = sp.single_pull(kegg_url=get_url)
        except rq.exceptions.Timeout:
            self._timed_out_urls.append(get_url)

            return

        if res is None:
            self._handle_failed_url(get_url=get_url)
        else:
            if get_url.multiple_entry_ids:
                entries: list = se.separate_entries(res=res.text, entry_field=self._entry_field)

                for entry_id, entry in zip(get_url.entry_ids, entries):
                    self._save_entry(entry_id=entry_id, entry=entry)
            else:
                [entry_id] = get_url.entry_ids
                entry: t.Union[str, bytes] = res.content if self._is_binary() else res.text
                self._save_entry(entry_id=entry_id, entry=entry)

        # Multiprocessing pickles this class such that it's deep-copied
        # This means that the successful and failed entry IDs won't be in the original class
        # So we return the successes and failures from this copy and add it to the result of the multiprocessing
        return self._successful_entry_ids, self._failed_entry_ids

    def _handle_failed_url(self, get_url: ku.GetKEGGurl):
        if get_url.multiple_entry_ids:
            for split_url in get_url.split_entries():
                self._pull_and_save(get_url=split_url)
        else:
            [entry_id] = get_url.entry_ids
            self._failed_entry_ids.append(entry_id)


    def _save_entry(self, entry_id: str, entry: t.Union[str, bytes]):
        file_extension = 'txt' if self._entry_field is None else self._entry_field
        file_path = os.path.join(self._output_dir, f'{entry_id}.{file_extension}')
        save_type = 'wb' if self._is_binary() else 'w'

        with open(file_path, save_type) as f:
            f.write(entry)

        self._successful_entry_ids.append(entry_id)

    def _is_binary(self) -> bool:
        return self._entry_field == 'image'
