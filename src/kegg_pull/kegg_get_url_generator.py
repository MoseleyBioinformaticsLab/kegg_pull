import logging

from src.kegg_pull.kegg_url import GetKEGGurl
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

        # TODO: Complete implementation

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
