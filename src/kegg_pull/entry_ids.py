"""
Pulling Lists of KEGG Entry IDs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for pulling lists of KEGG entry IDs from the KEGG REST API.
"""
import typing as t

from . import rest as r


def from_database(database_name: str, kegg_rest: r.KEGGrest = None) -> list:
    """ Pulls the KEGG entry IDs of a given database.

    :param database_name: The KEGG database to pull the entry IDs from.
    :param kegg_rest: Optional KEGGrest object. If None, one is created with the default parameters.
    :return: The list of resulting entry IDs.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _process_response(method='list', kegg_rest=kegg_rest, database_name=database_name)


def _process_response(method: str, kegg_rest: t.Union[r.KEGGrest, None], **kwargs) -> list:
    """ Extracts the entry IDs from a KEGG response if successful, else raises an exception. The KEGG response arrives from calling
    an entry IDs related method on a KEGGrest object.

    :param method: The method to call on the KEGGrest object.
    :param kegg_rest: The KEGGrest object to call the method on. If None, one is created with the default parameters.
    :param kwargs: The arguments to pass into the KEGGrest method.
    :return: The list of KEGG entry IDs.
    :raises RuntimeError: Raised if the KEGG response indicates a failure or time out.
    """
    kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()
    method: t.Callable = kegg_rest.__getattribute__(method)
    kegg_response: r.KEGGresponse = method(**kwargs)

    if kegg_response.status == r.KEGGresponse.Status.FAILED:
        raise RuntimeError(
            f'The KEGG request failed to pull the entry IDs from the following URL: {kegg_response.kegg_url.url}'
        )
    elif kegg_response.status == r.KEGGresponse.Status.TIMEOUT:
        raise RuntimeError(
            f'The KEGG request timed out while trying to pull the entry IDs from the following URL: '
            f'{kegg_response.kegg_url.url}'
        )

    entry_ids: list = _parse_entry_ids_string(entry_ids_string=kegg_response.text_body)

    return entry_ids


def _parse_entry_ids_string(entry_ids_string: str) -> list:
    """ Parses the entry IDs contained in a string.

    :param entry_ids_string: The string containing the entry IDs.
    :return: The list of parsed entry IDs.
    """
    entry_ids: list = entry_ids_string.strip().split('\n')
    entry_ids = [entry_id.split('\t')[0].strip() for entry_id in entry_ids if entry_id.strip() != '']

    return entry_ids


def from_file(file_path: str) -> list:
    """ Loads KEGG entry IDs that are listed in a file with one entry ID on each line.

    :param file_path: The path to the file containing the entry IDs.
    :return: The list of entry IDs.
    :raises ValueError: Raised if the file is empty.
    """
    with open(file_path, 'r') as file:
        entry_ids: str = file.read()

        if entry_ids == '':
            raise ValueError(f'Attempted to load entry IDs from {file_path}. But the file is empty')

        entry_ids: list = _parse_entry_ids_string(entry_ids_string=entry_ids)

    return entry_ids


def from_keywords(database_name: str, keywords: list, kegg_rest: r.KEGGrest = None) -> list:
    """ Pulls entry IDs from a KEGG database based on keywords searched in the entries.

    :param database_name: The name of the database to pull entry IDs from.
    :param keywords: The keywords to search entries in the database with.
    :param kegg_rest: Optional KEGGrest object. If None, one is created with the default parameters.
    :return: The list of entry IDs.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _process_response(method='keywords_find', kegg_rest=kegg_rest, database_name=database_name, keywords=keywords)


def from_molecular_attribute(
    database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None, molecular_weight: t.Union[int, tuple] = None,
    kegg_rest: r.KEGGrest = None
) -> list:
    """ Pulls entry IDs from a KEGG database containing chemical entries based on one (and only one) of three molecular attributes of the entries.

    :param database_name: The name of the database containing chemical entries.
    :param formula: The chemical formula to search for.
    :param exact_mass: The exact mass of the compound to search for (a single value or a range).
    :param molecular_weight: The molecular weight of the compound to search for (a single value or a range).
    :param kegg_rest: Optional KEGGrest object. If None, one is created with the default parameters.
    :return: The list of entry IDs.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _process_response(
        method='molecular_find', kegg_rest=kegg_rest, database_name=database_name, formula=formula, exact_mass=exact_mass,
        molecular_weight=molecular_weight
    )
