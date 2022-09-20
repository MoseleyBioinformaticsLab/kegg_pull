"""
Pulling, Parsing, and Saving KEGG Entries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for pulling KEGG entries from the KEGG REST API, parsing them, and saving the entries as files.
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
    """The collections of entry IDs, each of which resulted in a particular KEGG Response status after a pull."""

    def __init__(self) -> None:
        self._successful_entry_ids = []
        self._failed_entry_ids = []
        self._timed_out_entry_ids = []

    def __repr__(self):
        def get_entry_ids_repr(entry_ids) -> str:
            return ', '.join(entry_ids) if len(entry_ids) > 0 else 'none'

        successful_entry_ids: str = get_entry_ids_repr(entry_ids=self.successful_entry_ids)
        failed_entry_ids: str = get_entry_ids_repr(entry_ids=self.failed_entry_ids)
        timed_out_entry_ids: str = get_entry_ids_repr(entry_ids=self.timed_out_entry_ids)

        return f'Successful Entry Ids: {successful_entry_ids}\n' \
               f'Failed Entry Ids: {failed_entry_ids}\n' \
               f'Timed Out Entry Ids: {timed_out_entry_ids}'

    @property
    def successful_entry_ids(self) -> tuple:
        """The IDs of entries successfully pulled."""
        return tuple(self._successful_entry_ids)

    @property
    def failed_entry_ids(self) -> tuple:
        """The IDs of entries that failed to be pulled."""
        return tuple(self._failed_entry_ids)

    @property
    def timed_out_entry_ids(self) -> tuple:
        """The IDs of entries that timed out before being pulled."""
        return tuple(self._timed_out_entry_ids)

    def add_entry_ids(self, *entry_ids, status: r.KEGGresponse.Status) -> None:
        """ Adds entry IDs of a given status to the pull result.

        :param entry_ids: The entry IDs to add.
        :param status: The status resulting from attempting to pull the entries of the given IDs.
        """
        if status == r.KEGGresponse.Status.SUCCESS:
            self._successful_entry_ids.extend(entry_ids)
        elif status == r.KEGGresponse.Status.FAILED:
            self._failed_entry_ids.extend(entry_ids)
        else:
            self._timed_out_entry_ids.extend(entry_ids)

    def merge_pull_results(self, other) -> None:
        """ Combines two pull results into one.

        :param other: The pull result to combine into this one.
        """
        self._successful_entry_ids.extend(other.successful_entry_ids)
        self._failed_entry_ids.extend(other.failed_entry_ids)
        self._timed_out_entry_ids.extend(other.timed_out_entry_ids)


class SinglePull:
    """Class capable of performing a single request to the KEGG REST API for pulling up to a maximum number of entries."""

    class _AbstractEntrySaver(abc.ABC):
        """Abstract class for saving KEGG entries as files."""

        def save(self, entry_id: str, entry: t.Union[str, bytes], entry_field: str) -> None:
            """ Saves a KEGG entry as a file.

            :param entry_id: The entry ID (part of the file name).
            :param entry: The entry to save (contents of the file).
            :param entry_field: The particular field of the entry (file extension).
            """
            file_extension = 'txt' if entry_field is None else entry_field
            file_name = f'{entry_id}.{file_extension}'
            self._save(file_name=file_name, entry=entry)

        @abc.abstractmethod
        def _save(self, file_name: str, entry: t.Union[str, bytes]) -> None:
            """ Saves a KEGG entry in the particular manner of the child class.

            :param file_name: The name of the file in which the KEGG entry is saved.
            :param entry: The entry to save (contents of the file).
            """
            pass  # pragma: no cover

    class _DirectoryEntrySaver(_AbstractEntrySaver):
        """Class that saves KEGG entries in a directory."""

        def __init__(self, output_dir: str) -> None:
            """
            :param output_dir: The directory in which to save the KEGG entries.
            """
            if not os.path.isdir(output_dir):
                os.mkdir(output_dir)

            self._output_dir = output_dir

        def _save(self, file_name: str, entry: t.Union[str, bytes]) -> None:
            """ Saves a KEGG entry in a file within a directory.

            :param file_name: The name of the file to save in the directory.
            :param entry: The entry to save (content of the file).
            """
            file_path = os.path.join(self._output_dir, file_name)
            save_type = 'wb' if type(entry) is bytes else 'w'

            with open(file_path, save_type) as file:
                file.write(entry)

    class _ZipEntrySaver(_AbstractEntrySaver):
        """Class that saves KEGG entries in a ZIP file."""

        def __init__(self, zip_file: str) -> None:
            """
            :param zip_file: The path to the zip file to save the entries in.
            """
            self._zip_file = zip_file

        def _save(self, file_name: str, entry: t.Union[str, bytes]) -> None:
            """ Saves a KEGG entry in a zip file.

            :param file_name: The name of the file to save.
            :param entry: The entry to save (contents of file).
            """
            with zf.ZipFile(self._zip_file, 'a') as zip_file:
                zip_file.writestr(file_name, entry)

    def __init__(self, output_dir: str, kegg_rest: r.KEGGrest = None, entry_field: str = None) -> None:
        """
        :param output_dir: Path to the location where entries are saved (treated like a zip file if ends in .zip, else a directory).
        :param kegg_rest: Optional KEGGrest object used to make the requests to the KEGG REST API (a KEGGrest object with the default settings is created if one is not provided).
        :param entry_field: Optional KEGG entry field to pull.
        """
        if output_dir.endswith('.zip'):
            self._entry_saver = SinglePull._ZipEntrySaver(zip_file=output_dir)
        else:
            self._entry_saver = SinglePull._DirectoryEntrySaver(output_dir=output_dir)

        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()
        self.entry_field = entry_field


    def pull(self, entry_ids: list) -> PullResult:
        """ Makes a single request to the KEGG REST API to pull one or more entries and save them as files.

        :param entry_ids: The IDs of the entries to pull and save.
        :return: The pull result.
        """
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

    def _save_multi_entry_response(self, kegg_response: r.KEGGresponse, pull_result: PullResult) -> None:
        """ Saves multiple entries within a KEGG response.

        :param kegg_response: The response from KEGG with multiple entries.
        :param pull_result: The pull result to update based on the status of the pull(s).
        """
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
        """ Separates the entries in a multi-entry response from KEGG.

        :param concatenated_entries: The response body with all the entries together.
        :return: The separated KEGG entries.
        """
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
        """ Separates KEGG entries that are separated by a deliminator for nucleotide and amino acid sequence entries.
        :param concatenated_entries: The response body with the gene-related entries together.
        :return: The separated gene-related entries.
        """
        entries: list = concatenated_entries.split('>')

        if len(entries) > 1:
            return entries[1:]
        else:
            return entries

    @staticmethod
    def _mol_separator(concatenated_entries: str) -> list:
        """ Separates mol entries.

        :param concatenated_entries: The response body with the mol entries together.
        :return: The separated mole entries.
        """
        return SinglePull._split_and_remove_last(concatenated_entries=concatenated_entries, deliminator='$$$$')

    @staticmethod
    def _split_and_remove_last(concatenated_entries: str, deliminator: str) -> list:
        """ Splits entries based on a deliminator and removes the resulting empty string at the end of the list.

        :param concatenated_entries: The response body with the entries together.
        :param deliminator: The deliminator that separates the entries and is at the end of the response body.
        :return: The separated entries with the empty string removed.
        """
        entries: list = concatenated_entries.split(deliminator)

        if len(entries) > 1:
            return entries[:-1]
        else:
            return entries

    @staticmethod
    def _standard_separator(concatenated_entries: str) -> list:
        """ The separation method for most types of KEGG entries.

        :param concatenated_entries: The response body with the KEGG entries together.
        :return: The separated entries.
        """
        return SinglePull._split_and_remove_last(concatenated_entries=concatenated_entries, deliminator='///')

    def _pull_separate_entries(self, get_url: ku.GetKEGGurl, pull_result: PullResult) -> None:
        """ Pulls one entry at a time for a Get KEGG URL that has multiple entry IDs.

        :param get_url: The Get KEGG URL with multiple entry IDs to pull one at a time.
        :param pull_result: The pull result to update based on the success of the pulling.
        """
        for entry_id in get_url.entry_ids:
            kegg_response: r.KEGGresponse = self._kegg_rest.get(entry_ids=[entry_id], entry_field=self.entry_field)

            if kegg_response.status == r.KEGGresponse.Status.SUCCESS:
                self._save_single_entry_response(kegg_response=kegg_response, pull_result=pull_result)
            else:
                pull_result.add_entry_ids(entry_id, status=kegg_response.status)

    def _save_single_entry_response(self, kegg_response: r.KEGGresponse, pull_result: PullResult) -> None:
        """ Saves the entry in a KEGG response that contains only one entry.

        :param kegg_response: The KEGG response that only has one entry.
        :param pull_result: The pull result to update with the successful entry ID.
        """
        get_url: ku.GetKEGGurl = kegg_response.kegg_url
        [entry_id] = get_url.entry_ids
        pull_result.add_entry_ids(entry_id, status=r.KEGGresponse.Status.SUCCESS)

        if ku.GetKEGGurl.is_binary(entry_field=self.entry_field):
            entry: bytes = kegg_response.binary_body
        else:
            entry: str = kegg_response.text_body

        self._entry_saver.save(entry_id=entry_id, entry=entry, entry_field=self.entry_field)


    def _handle_unsuccessful_url(self, kegg_response: r.KEGGresponse, pull_result: PullResult) -> None:
        """ Handles an unsuccessful pull (failed or timed out).

        :param kegg_response: The KEGG response resulting from a pull that was not successful.
        :param pull_result: The pull result to update based on how the unsuccessful response is dealt with.
        """
        get_url: ku.GetKEGGurl = kegg_response.kegg_url
        status: r.KEGGresponse.Status = kegg_response.status

        if get_url.multiple_entry_ids:
            self._pull_separate_entries(get_url=get_url, pull_result=pull_result)
        else:
            [entry_id] = get_url.entry_ids
            pull_result.add_entry_ids(entry_id, status=status)


class AbstractMultiplePull(abc.ABC):
    """Abstract class that makes multiple requests to the KEGG REST API to pull and save entries of an unlimited amount."""

    def __init__(self, single_pull: SinglePull, force_single_entry: bool = False) -> None:
        """
        :param single_pull: The SinglePull object used for each pull.
        :param force_single_entry: Determines whether to pull only one entry at a time regardless of the entry field specified in the SinglePull argument.
        """
        self._single_pull = single_pull
        self._force_single_entry = force_single_entry

    def pull(
        self, entry_ids: list, entry_field: t.Optional[str] = '', force_single_entry: t.Optional[bool] = None
    ) -> PullResult:
        """ Makes multiple requests to the KEGG REST API for an unlimited amount of entry IDs.

        :param entry_ids: The IDs of the entries that are split into multiple pulls.
        :param entry_field: An optional field of the entries to pull.
        :param force_single_entry: If provided, updates the force_single_single_entry value of this AbstractMultiplePull object for this call of pull.
        :return: The pull result.
        """
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
        """ Gets the number of entries for each Get KEGG URL used to make the pulls.

        :param force_single_entry: If true, returns 1.
        :param entry_field: If the entry field can only be pulled 1 at a time, return 1.
        :return: 1 if the above specifications are true, else the maximum number of entries per Get URL.
        """
        if force_single_entry:
            return 1
        elif ku.GetKEGGurl.only_one_entry(entry_field=entry_field):
            return 1
        else:
            return ku.GetKEGGurl.MAX_ENTRY_IDS_PER_URL

    @abc.abstractmethod
    def _pull(self, grouped_entry_ids: list) -> PullResult:
        """ Pulls the entries of specified IDs in the manner of the extended concrete class.

        :param grouped_entry_ids: List of lists of entry IDs, with each list being below or equal to the number allowed per Get KEGG URL.
        :return: The pull result.
        """
        pass  # pragma: no cover


class SingleProcessMultiplePull(AbstractMultiplePull):
    """Class that makes multiple requests to the KEGG REST API to pull entries within a single process."""

    def _pull(self, grouped_entry_ids: list) -> PullResult:
        """ Makes multiple requests to the KEGG REST API to pull entries within a single process.

        :param grouped_entry_ids: List of lists of entry IDs, with each list being below or equal to the number allowed per Get KEGG URL.
        :return: The pull result
        """
        multiple_pull_result = PullResult()

        for entry_id_group in grouped_entry_ids:
            single_pull_result: PullResult = self._single_pull.pull(entry_ids=entry_id_group)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result


class MultiProcessMultiplePull(AbstractMultiplePull):
    """Class that makes multiple requests to the KEGG REST API to pull entries within multiple processes."""

    def __init__(self, single_pull: SinglePull, n_workers: int, force_single_entry: bool = False):
        """
        :param single_pull: The SinglePull object used for each pull.
        :param force_single_entry: Determines whether to pull only one entry at a time despite the entry field specified in the SinglePull argument.
        :param n_workers: The number of processes to use.
        """
        super(MultiProcessMultiplePull, self).__init__(single_pull=single_pull, force_single_entry=force_single_entry)
        self._n_workers = n_workers if n_workers is not None else os.cpu_count()

    def _pull(self, grouped_entry_ids: list) -> PullResult:
        """ Makes multiple requests to the KEGG REST API to pull entries within multiple processes.

        :param grouped_entry_ids: List of lists of entry IDs, with each list being below or equal to the number allowed per Get KEGG URL.
        :return: The pull result
        """
        multiple_pull_result = PullResult()
        args = [(entry_ids, self._single_pull) for entry_ids in grouped_entry_ids]
        chunk_size: int = min(len(grouped_entry_ids) // self._n_workers, 10)

        if chunk_size == 0:
            chunk_size = 1

        with mp.Pool(self._n_workers) as pool:
            results: list = pool.starmap(_get_single_pull_result, args, chunksize=chunk_size)

        for result in results:
            single_pull_result: PullResult = p.loads(result)
            multiple_pull_result.merge_pull_results(other=single_pull_result)

        return multiple_pull_result


def _get_single_pull_result(entry_ids: list, single_pull: SinglePull) -> bytes:
    """ Makes a request to the REST KEGG API to pull one or more entries.

    :param entry_ids: The IDs of the entries to pull.
    :param single_pull: The SinglePull object used to make the pull.
    :return: The pull result.
    """
    single_pull_result: PullResult = single_pull.pull(entry_ids=entry_ids)

    return p.dumps(single_pull_result)
