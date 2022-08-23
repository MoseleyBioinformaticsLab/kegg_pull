"""
Usage:
    kegg_pull pull -h | --help
    kegg_pull pull multiple (--database-name=<database-name>|--file-path=<file-path>) [--force-single-entry] [--multi-process] [--n-workers=<n-workers>] [--output-dir=<output_dir>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>] [--zip]
    kegg_pull pull single (--entry-ids=<entry-ids>|--file-path=<file-path>) [--output-dir=<output_dir>] [--entry-field=<entry-field>] [--n-tries=<n-tries>] [--time-out=<time-out>] [--sleep-time=<sleep-time>] [--zip]

Options:
    -h --help                           Show this help message.
    multiple                            Pull, separate, and store as many entries as requested via multiple automated requests to the KEGG web API. Useful when the number of entries requested is well above the maximum that KEGG allows for a single request.
    --database-name=<database-name>     The KEGG database from which to get a list of entry IDs to pull.
    --file-path=<file-path>             Path to a file containing a list of entry IDs to pull, with one entry ID on each line.
    --force-single-entry                Forces pulling only one entry at a time for every request to the KEGG web API. This flag is automatically set if --database-name is "brite".
    --multi-process                     If set, the entries are pulled across multiple processes to increase speed. Otherwise, the entries are pulled sequentially in a single process.
    --n-workers=<n-workers>             The number of sub-processes to create when pulling. Defaults to the number of cores available. Ignored if --multi-process is not set.
    --output-dir=<output_dir>           The directory where the pulled KEGG entries will be stored. Defaults to the current working directory. If ends in .zip, entries are saved to a zip archive instead of a directory.
    --entry-field=<entry-field>         Optional field to extract from the entries pulled rather than the standard flat file format (or "htext" in the case of brite entries).
    --n-tries=<n-tries>                 The number of times to attempt a KEGG request before marking it as timed out or failed. Defaults to 3.
    --time-out=<time-out>               The number of seconds to wait for a KEGG request before marking it as timed out. Defaults to 60.
    --sleep-time=<sleep-time>           The amount of time to wait after a KEGG request times out before attempting it again. Defaults to 0.
    single                              Pull, separate, and store one or more KEGG entries via a single request to the KEGG web API. Useful when the number of entries requested is less than or equal to the maximum that KEGG allows for a single request.
    --entry-ids=<entry-ids>             Comma separated list of entry IDs to pull in a single request (e.g. --entry-ids=id1,id2,id3 etc.).
"""
import multiprocessing as mp
import os
import abc
import typing as t
import pickle as p
import docopt as d
import zipfile as zf

from . import kegg_url as ku
from . import rest as r
from . import entry_ids as ei
from . import utils as u


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

    def add_entry_ids(self, *entry_ids, status: r.KEGGresponse.Status):
        if status == r.KEGGresponse.Status.SUCCESS:
            self._successful_entry_ids.extend(entry_ids)
        elif status == r.KEGGresponse.Status.FAILED:
            self._failed_entry_ids.extend(entry_ids)
        elif status == r.KEGGresponse.Status.TIMEOUT:
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
            pass

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
        return concatenated_entries.split('>')[1:]

    @staticmethod
    def _mol_separator(concatenated_entries: str) -> list:
        return SinglePull._split_and_remove_last(concatenated_entries=concatenated_entries, deliminator='$$$$')

    @staticmethod
    def _split_and_remove_last(concatenated_entries: str, deliminator: str) -> list:
        return concatenated_entries.split(deliminator)[:-1]

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
    def _pull(self, grouped_entry_ids: list):
        pass


class SingleProcessMultiplePull(AbstractMultiplePull):
    def _pull(self, grouped_entry_ids: list):
        multiple_pull_result = PullResult()

        for entry_id_group in grouped_entry_ids:
            single_pull_result: PullResult = self._single_pull.pull(entry_ids=entry_id_group)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result


class MultiProcessMultiplePull(AbstractMultiplePull):
    def __init__(self, single_pull: SinglePull, force_single_entry: bool = False, n_workers: int = os.cpu_count()):
        super(MultiProcessMultiplePull, self).__init__(single_pull=single_pull, force_single_entry=force_single_entry)
        self._n_workers = n_workers

    def _pull(self, grouped_entry_ids: list):
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


def main():
    args: dict = d.docopt(__doc__)

    if args['--help']:
        print(__doc__)
        exit(0)

    n_tries: str = int(args['--n-tries']) if args['--n-tries'] is not None else None
    time_out: str = int(args['--time-out']) if args['--time-out'] is not None else None
    sleep_time: str = float(args['--sleep-time']) if args['--sleep-time'] is not None else None
    kegg_rest = r.KEGGrest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    output_dir: str = args['--output-dir'] if args['--output-dir'] is not None else '.'
    entry_field: str = args['--entry-field']
    puller = SinglePull(output_dir=output_dir, kegg_rest=kegg_rest, entry_field=entry_field)
    database_name: str = args['--database-name']
    force_single_entry: bool = args['--force-single-entry']

    if database_name is not None:
        if database_name == 'brite':
            force_single_entry = True

        entry_ids_getter = ei.EntryIdsGetter(kegg_rest=kegg_rest)
        entry_ids: list = entry_ids_getter.from_database(database_name=database_name)
    elif args['--file-path'] is not None:
        file_path: str = args['--file-path']
        entry_ids: list = ei.EntryIdsGetter.from_file(file_path=file_path)
    else:
        entry_ids_string: str = args['--entry-ids']
        entry_ids: list = u.split_comma_separated_list(list_string=entry_ids_string)

    if args['multiple']:
        if args['--multi-process']:
            n_workers = int(args['--n-workers']) if args['--n-workers'] is not None else None

            puller = MultiProcessMultiplePull(
                single_pull=puller, force_single_entry=force_single_entry, n_workers=n_workers
            )
        else:
            puller = SingleProcessMultiplePull(single_pull=puller, force_single_entry=force_single_entry)

    pull_result: PullResult = puller.pull(entry_ids=entry_ids)

    with open('pull-results.txt', 'w') as file:
        _write_entry_ids(file=file, entry_id_type='Successful', entry_ids=pull_result.successful_entry_ids)
        _write_entry_ids(file=file, entry_id_type='Failed', entry_ids=pull_result.failed_entry_ids)
        _write_entry_ids(file=file, entry_id_type='Timed Out', entry_ids=pull_result.timed_out_entry_ids)


def _write_entry_ids(file: t.TextIO, entry_id_type: str, entry_ids: list):
    file.write(f'### {entry_id_type} Entry IDs ###\n')

    for entry_id in entry_ids:
        file.write(entry_id + '\n')
