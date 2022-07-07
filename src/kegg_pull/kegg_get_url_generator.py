import logging
from requests import Response

from src.kegg_pull.kegg_url import ListKEGGurl, GetKEGGurl
from src.kegg_pull.pull_single_from_kegg import pull_single_from_kegg

MAX_KEGG_ENTRY_IDS_PER_GET_URL: int = 10


class KEGGgetURLgenerator:
    def __init__(self, database_type: str = None, entry_id_list_path: str = None, entry_field: str = None):
        self._validate(database_type=database_type, entry_id_list_path=entry_id_list_path)

        if entry_field is not None and GetKEGGurl.can_only_pull_one_entry(entry_field=entry_field):
            self._n_entries_per_url = 1
        else:
            self._n_entries_per_url = MAX_KEGG_ENTRY_IDS_PER_GET_URL

        self._entry_field = entry_field

        if database_type is not None:
            self._entry_id_list: list = self._get_entry_id_list_from_kegg_list_api_operation(
                database_type=database_type
            )
        else:
            self._entry_id_list: list = self._get_entry_id_list_from_file(entry_id_list_path=entry_id_list_path)

    @staticmethod
    def _validate(database_type: str, entry_id_list_path: str):
        if database_type is not None and entry_id_list_path is not None:
            logging.warning(
                'Both a database type and file path to an entry ID list are specified. Ignoring the entry ID list '
                'path... '
            )
        elif database_type is None and entry_id_list_path is None:
            raise ValueError(
                'Required: Either a file containing a list of KEGG entry IDs or the name of a KEGG database from which '
                'the entry IDs can be pulled. Neither are provided'
            )

    @staticmethod
    def _get_entry_id_list_from_kegg_list_api_operation(database_type: str) -> list:
        list_url = ListKEGGurl(database_type=database_type)
        res: Response = pull_single_from_kegg(kegg_url=list_url)
        entry_ids: list = KEGGgetURLgenerator._parse_entry_ids_string(entry_ids_string=res.text)

        # We empirically determined that each line consists of the entry ID followed by more info separated by a tab
        for i, entry_id in enumerate(entry_ids):
            entry_id: str = entry_id.split('\t')[0]
            entry_ids[i] = entry_id

        return entry_ids

    @staticmethod
    def _parse_entry_ids_string(entry_ids_string: str) -> list:
        entry_ids: list = entry_ids_string.strip().split('\n')

        return entry_ids

    @staticmethod
    def _get_entry_id_list_from_file(entry_id_list_path: str) -> list:
        with open(entry_id_list_path, 'r') as f:
            entry_ids: str = f.read()
            entry_ids: list = KEGGgetURLgenerator._parse_entry_ids_string(entry_ids_string=entry_ids)

        return entry_ids

    def __iter__(self):
        for i in range(0, len(self._entry_id_list), self._n_entries_per_url):
            entry_ids: list = self._entry_id_list[i:i+self._n_entries_per_url]
            get_kegg_url = GetKEGGurl(entry_ids=entry_ids, entry_field=self._entry_field)

            yield get_kegg_url
