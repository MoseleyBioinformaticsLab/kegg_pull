import typing as t

from . import kegg_request as kr
from . import kegg_url as ku


def from_database(database_name: str) -> list:
    return _from_kegg_api_operation(KEGGurl=ku.ListKEGGurl, database_name=database_name)

def _from_kegg_api_operation(**kwargs) -> list:
    kegg_request = kr.KEGGrequest()
    kegg_response: kr.KEGGresponse = kegg_request.execute_api_operation(**kwargs)

    if kegg_response.status == kr.KEGGresponse.Status.FAILED:
        raise RuntimeError(
            f'The KEGG request failed to get the entry IDs from the following URL: {kegg_response.kegg_url.url}'
        )
    elif kegg_response.status == kr.KEGGresponse.Status.TIMEOUT:
        raise RuntimeError(
            f'The KEGG request timed out while trying to get the entry IDs from the following URL: '
            f'{kegg_response.kegg_url.url}'
        )

    entry_ids: list = _parse_entry_ids_string(entry_ids_string=kegg_response.text_body)

    return entry_ids


def from_file(entry_ids_file_path: str) -> list:
    with open(entry_ids_file_path, 'r') as f:
        entry_ids: str = f.read()

        if entry_ids == '':
            raise ValueError(f'Attempted to get entry IDs from {entry_ids_file_path}. But the file is empty')

        entry_ids: list = _parse_entry_ids_string(entry_ids_string=entry_ids)

    return entry_ids


def _parse_entry_ids_string(entry_ids_string: str) -> list:
    entry_ids: list = entry_ids_string.strip().split('\n')
    entry_ids = [entry_id.split('\t')[0].strip() for entry_id in entry_ids]

    return entry_ids


def from_keywords(database_name: str, keywords: list) -> list:
    return _from_kegg_api_operation(KEGGurl=ku.KeywordsFindKEGGurl, database_name=database_name, keywords=keywords)


def from_molecular_attribute(
    database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
    molecular_weight: t.Union[int, tuple] = None
):
    return _from_kegg_api_operation(
        KEGGurl=ku.MolecularFindKEGGurl, database_name=database_name, formula=formula, exact_mass=exact_mass,
        molecular_weight=molecular_weight
    )
