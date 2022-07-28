import logging as l

from . import kegg_request as kr
from . import kegg_url as ku


def from_database(database_name: str) -> list:
    list_url = ku.ListKEGGurl(database_name=database_name)
    kegg_request = kr.KEGGrequest()
    response: kr.KEGGresponse = kegg_request.get(url=list_url.url)

    if response.status == kr.KEGGresponse.Status.FAILED:
        raise RuntimeError(f'The KEGG request failed to get the entry IDs of the {database_name} database')
    elif response.status == kr.KEGGresponse.Status.TIMEOUT:
        raise RuntimeError(
            f'The KEGG request timed out while trying to get the entry IDs of the {database_name} database'
        )

    entry_ids: list = _parse_entry_ids_string(entry_ids_string=response.text_body)

    return entry_ids


def from_file(file_path: str) -> list:
    with open(file_path, 'r') as f:
        entry_ids: str = f.read()

        if entry_ids == '':
            raise ValueError(f'Attempted to get entry IDs from {file_path}. But the file is empty')

        entry_ids: list = _parse_entry_ids_string(entry_ids_string=entry_ids)

    return entry_ids


def _parse_entry_ids_string(entry_ids_string: str) -> list:
    entry_ids: list = entry_ids_string.strip().split('\n')
    entry_ids = [entry_id.split('\t')[0].strip() for entry_id in entry_ids]

    return entry_ids


def from_string(entry_ids_string: str) -> list:
    entry_ids: list = entry_ids_string.split(',')

    if '' in entry_ids:
        l.warning(f'Blank entry IDs detected in the provided list: "{entry_ids_string}". Removing blank entry IDs...')
        entry_ids = [entry_id for entry_id in entry_ids if entry_id != '']

    return entry_ids
