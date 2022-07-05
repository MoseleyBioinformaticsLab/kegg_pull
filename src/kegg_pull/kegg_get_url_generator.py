import logging

from src.kegg_pull.generic_kegg_url import GenericKEGGurl
from src.kegg_pull.pull_single_from_kegg import pull_single_from_kegg

MAX_KEGG_ENTRY_IDS_PER_GET_URL: int = 10


class KEGGgetURLgenerator:
    def __init__(self, database_type: str = None, entry_id_list_path: str = None, pull_format: str = None):
        self._validate(database_type=database_type, entry_id_list_path=entry_id_list_path)

        if pull_format is not None and GenericKEGGurl.can_only_pull_one_entry(pull_format=pull_format):
            self._n_entries_per_url: int = MAX_KEGG_ENTRY_IDS_PER_GET_URL
        else:
            self._n_entries_per_url: int = 1

        self._pull_format: str = pull_format

    @staticmethod
    def _validate(database_type: str, entry_id_list_path: str, ):
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
