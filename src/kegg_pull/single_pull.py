import typing as t
import os

from . import kegg_url as ku
from . import web_request as wr
from . import pull_result as pr


class SinglePull:
    def __init__(self, output_dir: str, web_request: wr.WebRequest = None, entry_field: str = None):
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)

        self._output_dir = output_dir

        if web_request is None:
            web_request = wr.WebRequest()

        self._web_request = web_request
        self.entry_field = entry_field


    def pull(self, entry_ids: list) -> pr.PullResult:
        get_url = ku.GetKEGGurl(entry_ids=entry_ids, entry_field=self.entry_field)
        web_response: wr.WebResponse = self._web_request.get(url=get_url.url)
        pull_result = pr.PullResult()

        if web_response.status == wr.WebResponse.Status.SUCCESS:
            if get_url.multiple_entry_ids:
                self._save_multi_entry_response(web_response=web_response, get_url=get_url, pull_result=pull_result)
            else:
                self._save_single_entry_response(web_response=web_response, get_url=get_url, pull_result=pull_result)
        else:
            self._handle_unsuccessful_url(get_url=get_url, pull_result=pull_result, status=web_response.status)

        return pull_result

    def _save_multi_entry_response(
        self, web_response: wr.WebResponse, get_url: ku.GetKEGGurl, pull_result: pr.PullResult
    ):
        entries: list = self._separate_entries(concatenated_entries=web_response.text_body)

        if len(entries) < len(get_url.entry_ids):
            # If we did not get all the entries requested, process each entry one at a time
            self._pull_separate_entries(get_url=get_url, pull_result=pull_result)
        else:
            pull_result.add_entry_ids(*get_url.entry_ids, status=wr.WebResponse.Status.SUCCESS)

            for entry_id, entry in zip(get_url.entry_ids, entries):
                self._save_entry(entry_id=entry_id, entry=entry)

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

    def _pull_separate_entries(self, get_url: ku.GetKEGGurl, pull_result: pr.PullResult):
        for split_url in get_url.split_entries():
            [entry_id] = split_url.entry_ids
            web_response: wr.WebResponse = self._web_request.get(url=split_url.url)

            if web_response.status == wr.WebResponse.Status.SUCCESS:
                self._save_single_entry_response(web_response=web_response, get_url=get_url, pull_result=pull_result)
            else:
                pull_result.add_entry_ids(entry_id, status=web_response.status)

    def _save_single_entry_response(
        self, web_response: wr.WebResponse, get_url: ku.GetKEGGurl, pull_result: pr.PullResult
    ):
        [entry_id] = get_url.entry_ids
        pull_result.add_entry_ids(entry_id, status=wr.WebResponse.Status.SUCCESS)
        entry: t.Union[str, bytes] = web_response.binary_body if self._is_binary() else web_response.text_body
        self._save_entry(entry_id=entry_id, entry=entry)

    def _is_binary(self) -> bool:
        return self.entry_field == 'image'

    def _save_entry(self, entry_id: str, entry: t.Union[str, bytes]):
        file_extension = 'txt' if self.entry_field is None else self.entry_field
        file_path = os.path.join(self._output_dir, f'{entry_id}.{file_extension}')
        save_type = 'wb' if self._is_binary() else 'w'

        with open(file_path, save_type) as f:
            f.write(entry)

    def _handle_unsuccessful_url(
            self, get_url: ku.GetKEGGurl, pull_result: pr.PullResult, status: wr.WebResponse.Status
    ):
        if get_url.multiple_entry_ids:
            self._pull_separate_entries(get_url=get_url, pull_result=pull_result)
        else:
            [entry_id] = get_url.entry_ids
            pull_result.add_entry_ids(entry_id, status=status)
