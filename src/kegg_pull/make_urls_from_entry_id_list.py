import logging
import requests as rq

from . import kegg_url as ku
from . import single_pull as sp

SINGLE_ENTRY_DATABASES = {'brite'}
MAX_KEGG_ENTRY_IDS_PER_GET_URL: int = 10


def make_urls_from_entry_id_list(
    force_single_entry: bool, database_type: str = None, entry_id_list_path: str = None, entry_field: str = None
) -> list:
    _validate(database_type=database_type, entry_id_list_path=entry_id_list_path)

    if database_type is not None and database_type in SINGLE_ENTRY_DATABASES:
        force_single_entry = True

    n_entries_per_url: int = _get_n_entries_per_url(force_single_entry=force_single_entry, entry_field=entry_field)
    entry_id_list: list = _get_entry_id_list(database_type=database_type, entry_id_list_path=entry_id_list_path)

    return _make_urls_from_entry_id_list(
        entry_id_list=entry_id_list, n_entries_per_url=n_entries_per_url, entry_field=entry_field
    )


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


def _get_n_entries_per_url(force_single_entry: bool, entry_field: str) -> int:
    if force_single_entry:
        return 1
    elif ku.GetKEGGurl.can_only_pull_one_entry(entry_field=entry_field):
        return 1
    else:
        return MAX_KEGG_ENTRY_IDS_PER_GET_URL


def _get_entry_id_list(database_type: str, entry_id_list_path: str) -> list:
    if database_type is not None:
        return _get_entry_id_list_from_kegg_list_api_operation(database_type=database_type)
    else:
        return _get_entry_id_list_from_file(entry_id_list_path=entry_id_list_path)


def _get_entry_id_list_from_kegg_list_api_operation(database_type: str) -> list:
    list_url = ku.ListKEGGurl(database_type=database_type)
    res: rq.Response = sp.single_pull(kegg_url=list_url)
    entry_ids: list = _parse_entry_ids_string(entry_ids_string=res.text)

    # We empirically determined that each line consists of the entry ID followed by more info separated by a tab
    entry_ids = [entry_id.split('\t')[0] for entry_id in entry_ids]

    return entry_ids


def _parse_entry_ids_string(entry_ids_string: str) -> list:
    entry_ids: list = entry_ids_string.strip().split('\n')
    entry_ids = [entry_id.strip() for entry_id in entry_ids]

    return entry_ids


def _get_entry_id_list_from_file(entry_id_list_path: str) -> list:
    with open(entry_id_list_path, 'r') as f:
        entry_ids: str = f.read()
        entry_ids: list = _parse_entry_ids_string(entry_ids_string=entry_ids)

    return entry_ids


def _make_urls_from_entry_id_list(entry_id_list: list, n_entries_per_url: int, entry_field: str) -> list:
    get_urls = []

    for i in range(0, len(entry_id_list), n_entries_per_url):
        entry_ids: list = entry_id_list[i:i+n_entries_per_url]
        get_kegg_url = ku.GetKEGGurl(entry_ids=entry_ids, entry_field=entry_field)
        get_urls.append(get_kegg_url)

    return get_urls
