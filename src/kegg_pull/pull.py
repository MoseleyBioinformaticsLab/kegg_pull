"""
Pulling, Parsing, and Saving KEGG Entries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for getting KEGG entries from the KEGG REST API, parsing them, and saving the entries as files.
"""
import multiprocessing as mp
import os
import abc
import typing as t
import pickle as p
import zipfile as zf

from . import kegg_url as ku
from . import rest as r


class PullResult:
    """The collections of entry IDs that resulted in a particular KEGG Response status after a pull"""
    def __init__(self):
        self._successful_entry_ids = []
        self._failed_entry_ids = []
        self._timed_out_entry_ids = []

    @property
    def successful_entry_ids(self) -> tuple:
        return tuple(self._successful_entry_ids)

    @property
    def failed_entry_ids(self) -> tuple:
        return tuple(self._failed_entry_ids)

    @property
    def timed_out_entry_ids(self) -> tuple:
        return tuple(self._timed_out_entry_ids)

    def add_entry_ids(self, *entry_ids, status: r.KEGGresponse.Status):
        if status == r.KEGGresponse.Status.SUCCESS:
            self._successful_entry_ids.extend(entry_ids)
        elif status == r.KEGGresponse.Status.FAILED:
            self._failed_entry_ids.extend(entry_ids)
        else:
            self._timed_out_entry_ids.extend(entry_ids)

    def merge_pull_results(self, other):
        self._successful_entry_ids.extend(other.successful_entry_ids)
        self._failed_entry_ids.extend(other.failed_entry_ids)
        self._timed_out_entry_ids.extend(other.timed_out_entry_ids)


class SinglePull:
    class _AbstractEntrySaver(abc.ABC):
        def save(self, entry_id: str, entry: t.Union[str, bytes], entry_field: str):
            file_extension = 'txt' if entry_field is None else entry_field
            file_name = f'{entry_id}.{file_extension}'
            self._save(file_name=file_name, entry=entry)

        @abc.abstractmethod
        def _save(self, file_name: str, entry: t.Union[str, bytes]):
            pass  # pragma: no cover

    class _DirectoryEntrySaver(_AbstractEntrySaver):
        def __init__(self, output_dir: str):
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)

            self._output_dir = output_dir

        def _save(self, file_name: str, entry: t.Union[str, bytes]):
            file_path = os.path.join(self._output_dir, file_name)
            save_type = 'wb' if type(entry) is bytes else 'w'

            with open(file_path, save_type) as file:
                file.write(entry)

    class _ZipEntrySaver(_AbstractEntrySaver):
        def __init__(self, zip_file: str):
            self._zip_file = zip_file

        def _save(self, file_name: str, entry: t.Union[str, bytes]):
            with zf.ZipFile(self._zip_file, 'a') as zip_file:
                zip_file.writestr(file_name, entry)

    def __init__(self, output_dir: str, kegg_rest: r.KEGGrest = None, entry_field: str = None):
        if output_dir.endswith('.zip'):
            self._entry_saver = SinglePull._ZipEntrySaver(zip_file=output_dir)
        else:
            self._entry_saver = SinglePull._DirectoryEntrySaver(output_dir=output_dir)

        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()
        self.entry_field = entry_field


    def pull(self, entry_ids: list) -> PullResult:
        kegg_response: r.KEGGresponse = self._kegg_rest.get(entry_ids=entry_ids, entry_field=self.entry_field)
        get_url: ku.GetKEGGurl = kegg_response.kegg_url
        pull_result = PullResult()

        if kegg_response.status == r.KEGGresponse.Status.SUCCESS:
            if get_url.multiple_entry_ids:
                self._save_multi_entry_response(kegg_response=kegg_response, pull_result=pull_result)
            else:
                self._save_single_entry_response(kegg_response=kegg_response, pull_result=pull_result)
        else:
            self._handle_unsuccessful_url(kegg_response=kegg_response, pull_result=pull_result)

        return pull_result

    def _save_multi_entry_response(self, kegg_response: r.KEGGresponse, pull_result: PullResult):
        entries: list = self._separate_entries(concatenated_entries=kegg_response.text_body)
        get_url: ku.GetKEGGurl = kegg_response.kegg_url

        if len(entries) < len(get_url.entry_ids):
            # If we did not get all the entries requested, process each entry one at a time
            self._pull_separate_entries(get_url=get_url, pull_result=pull_result)
        else:
            pull_result.add_entry_ids(*get_url.entry_ids, status=r.KEGGresponse.Status.SUCCESS)

            for entry_id, entry in zip(get_url.entry_ids, entries):
                self._entry_saver.save(entry_id=entry_id, entry=entry, entry_field=self.entry_field)

    def _separate_entries(self, concatenated_entries: str) -> list:
        field_to_separator = {
            'aaseq': SinglePull._gene_separator, 'kcf': SinglePull._standard_separator,
            'mol': SinglePull._mol_separator, 'ntseq': SinglePull._gene_separator
        }

        if self.entry_field is None:
            separator = SinglePull._standard_separator
        else:
            separator = field_to_separator[self.entry_field]

        entries: list = separator(concatenated_entries=concatenated_entries)
        entries = [entry.strip() for entry in entries]

        return entries

    @staticmethod
    def _gene_separator(concatenated_entries: str) -> list:
        entries: list = concatenated_entries.split('>')

        if len(entries) > 1:
            return entries[1:]
        else:
            return entries

    @staticmethod
    def _mol_separator(concatenated_entries: str) -> list:
        return SinglePull._split_and_remove_last(concatenated_entries=concatenated_entries, deliminator='$$$$')

    @staticmethod
    def _split_and_remove_last(concatenated_entries: str, deliminator: str) -> list:
        entries: list = concatenated_entries.split(deliminator)

        if len(entries) > 1:
            return entries[:-1]
        else:
            return entries

    @staticmethod
    def _standard_separator(concatenated_entries: str) -> list:
        return SinglePull._split_and_remove_last(concatenated_entries=concatenated_entries, deliminator='///')

    def _pull_separate_entries(self, get_url: ku.GetKEGGurl, pull_result: PullResult):
        for entry_id in get_url.entry_ids:
            kegg_response: r.KEGGresponse = self._kegg_rest.get(entry_ids=[entry_id], entry_field=self.entry_field)

            if kegg_response.status == r.KEGGresponse.Status.SUCCESS:
                self._save_single_entry_response(kegg_response=kegg_response, pull_result=pull_result)
            else:
                pull_result.add_entry_ids(entry_id, status=kegg_response.status)

    def _save_single_entry_response(self, kegg_response: r.KEGGresponse, pull_result: PullResult):
        get_url: ku.GetKEGGurl = kegg_response.kegg_url
        [entry_id] = get_url.entry_ids
        pull_result.add_entry_ids(entry_id, status=r.KEGGresponse.Status.SUCCESS)

        if ku.GetKEGGurl.is_binary(entry_field=self.entry_field):
            entry: bytes = kegg_response.binary_body
        else:
            entry: str = kegg_response.text_body

        self._entry_saver.save(entry_id=entry_id, entry=entry, entry_field=self.entry_field)


    def _handle_unsuccessful_url(self, kegg_response: r.KEGGresponse, pull_result: PullResult):
        get_url: ku.GetKEGGurl = kegg_response.kegg_url
        status: r.KEGGresponse.Status = kegg_response.status

        if get_url.multiple_entry_ids:
            self._pull_separate_entries(get_url=get_url, pull_result=pull_result)
        else:
            [entry_id] = get_url.entry_ids
            pull_result.add_entry_ids(entry_id, status=status)


class AbstractMultiplePull(abc.ABC):
    def __init__(self, single_pull: SinglePull, force_single_entry: bool = False):
        self._single_pull = single_pull
        self._force_single_entry = force_single_entry

    def pull(
        self, entry_ids: list, entry_field: t.Optional[str] = '', force_single_entry: t.Optional[bool] = None
    ) -> PullResult:
        force_single_entry = force_single_entry if force_single_entry is not None else self._force_single_entry

        # If a new entry field is provided, update it
        if entry_field != '':
            self._single_pull.entry_field = entry_field

        entry_ids: list = self._group_entry_ids(
            entry_ids_to_group=entry_ids, force_single_entry=force_single_entry
        )

        return self._pull(grouped_entry_ids=entry_ids)

    def _group_entry_ids(self, entry_ids_to_group: list, force_single_entry: bool) -> list:
        group_size: int = AbstractMultiplePull._get_n_entries_per_url(
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
    def _pull(self, grouped_entry_ids: list) -> PullResult:
        pass  # pragma: no cover


class SingleProcessMultiplePull(AbstractMultiplePull):
    def _pull(self, grouped_entry_ids: list) -> PullResult:
        multiple_pull_result = PullResult()

        for entry_id_group in grouped_entry_ids:
            single_pull_result: PullResult = self._single_pull.pull(entry_ids=entry_id_group)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result


class MultiProcessMultiplePull(AbstractMultiplePull):
    def __init__(self, single_pull: SinglePull, force_single_entry: bool = False, n_workers: int = os.cpu_count()):
        super(MultiProcessMultiplePull, self).__init__(single_pull=single_pull, force_single_entry=force_single_entry)
        self._n_workers = n_workers

    def _pull(self, grouped_entry_ids: list) -> PullResult:
        multiple_pull_result = PullResult()
        args = [(entry_ids, self._single_pull) for entry_ids in grouped_entry_ids]
        chunk_size: int = len(grouped_entry_ids) // self._n_workers

        with mp.Pool(self._n_workers) as pool:
            results: list = pool.starmap(_get_single_pull_result, args, chunksize=chunk_size)

        for result in results:
            single_pull_result: PullResult = p.loads(result)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result


def _get_single_pull_result(entry_ids: list, single_pull: SinglePull) -> bytes:
    single_pull_result: PullResult = single_pull.pull(entry_ids=entry_ids)

    return p.dumps(single_pull_result)
