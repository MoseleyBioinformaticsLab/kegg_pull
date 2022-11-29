"""
Creating Dictionaries From KEGG Link Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for converting the output from the KEGG "link" REST operation into dictionaries linking the entry IDs from one database to the IDs of related entries.
"""
import typing as t

from . import rest as r
from . import kegg_url as ku


def database_link(target_database_name: str, source_database_name: str, kegg_rest: r.KEGGrest = None) -> dict:
    """ Converts the output of the KEGG "link" operation (of the form that links the entry IDs of one database to the entry IDs of
    another) into a dictionary.

    :param target_database_name: One of the two KEGG databases to pull linked entries from.
    :param source_database_name: The other KEGG database to link entries from the target database.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _to_dict(
        kegg_rest=kegg_rest, KEGGurl=ku.DatabaseLinkKEGGurl, target_database_name=target_database_name,
        source_database_name=source_database_name
    )


def _to_dict(kegg_rest: t.Union[r.KEGGrest, None], KEGGurl: type, **kwargs) -> dict:
    """ Converts output from the KEGG "link" operation into a dictionary.

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :param KEGGurl: The class extending AbstractKEGGurl used to form the URL for the link operation.
    :param kwargs: The keyword arguments for constructing the URL.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    kegg_response: r.KEGGresponse = r.request_and_check_error(kegg_rest=kegg_rest, KEGGurl=KEGGurl, **kwargs)
    linked_ids = {}

    for link in kegg_response.text_body.strip().split('\n'):
        [link_from_id, link_to_id] = link.split('\t')

        if link_from_id in linked_ids.keys():
            linked_ids[link_from_id].add(link_to_id)
        else:
            linked_ids[link_from_id] = {link_to_id}

    return linked_ids


def entries_link(target_database_name: str, entry_ids: list, kegg_rest: r.KEGGrest = None) -> dict:
    """ Converts the output of the KEGG "link" operation (of the form that links the entry IDs of a database to specific provided
    entry IDs) to a dictionary.

    :param target_database_name: The KEGG database to find links to the provided entries.
    :param entry_ids: The IDs of the entries to link to entries in the target database.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _to_dict(
        kegg_rest=kegg_rest, KEGGurl=ku.EntriesLinkKEGGurl, target_database_name=target_database_name, entry_ids=entry_ids
    )


def compound_to_pathway(add_glycans: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps compound entry IDs to related pathway IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=pathway_to_compound(add_glycans=add_glycans, kegg_rest=kegg_rest))


def reverse_mapping(mapping: dict) -> dict:
    """ Reverses the dictionary mapping entry IDs of one database to IDs of related entries, turning keys into values and values into keys.

    :param mapping: The dictionary, of entry IDs (strings) to sets of entry IDs, to reverse.
    :return: The reversed mapping.
    """
    reversed_mapping: dict = {}

    for key, values in mapping.items():
        for value in values:
            _add_to_dict(dictionary=reversed_mapping, key=value, values={key})

    return reversed_mapping


def _add_to_dict(dictionary: dict, key: str, values: set) -> None:
    """ Adds a set of values to a set mapped from a given key in a dictionary.

    :param dictionary: The dictionary mapping to sets, one of which the values will be added to.
    :param key: The key in the dictionary mapping to the set that the values will be added to.
    :param values: The values to add to the set mapped to by the key.
    """
    if key in dictionary.keys():
        dictionary[key].update(values)
    else:
        dictionary[key] = values


def pathway_to_compound(add_glycans: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps pathway entry IDs to related compound IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _database_to_compound(database='pathway', add_glycans=add_glycans, kegg_rest=kegg_rest)


def _database_to_compound(database: str, add_glycans, kegg_rest: t.Union[r.KEGGrest, None]) -> dict:
    """ Creates a dictionary that maps the entry IDs of a given KEGG database to related compound IDs.

    :param database: The database with IDs to map to compound IDs.
    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    database_to_compound: dict = database_link(target_database_name='compound', source_database_name=database, kegg_rest=kegg_rest)

    if add_glycans:
        database_to_glycan: dict = database_link(target_database_name='glycan', source_database_name=database, kegg_rest=kegg_rest)
        glycan_to_compound: dict = database_link(target_database_name='compound', source_database_name='glycan', kegg_rest=kegg_rest)

        for entry_id, glycan_ids in database_to_glycan.items():
            for glycan_id in glycan_ids:
                if glycan_id in glycan_to_compound.keys():
                    glycan_compound_ids: set = glycan_to_compound[glycan_id]
                    _add_to_dict(dictionary=database_to_compound, key=entry_id, values=glycan_compound_ids)

    return database_to_compound


def compound_to_reaction(add_glycans: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps compound entry IDs to related reaction IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=reaction_to_compound(add_glycans=add_glycans, kegg_rest=kegg_rest))


def reaction_to_compound(add_glycans: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps reaction entry IDs to related compound IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _database_to_compound(database='reaction', add_glycans=add_glycans, kegg_rest=kegg_rest)

def compound_to_gene(add_glycans: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps compound entry IDs to related gene IDs (from the KEGG ko database).

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=gene_to_compound(add_glycans=add_glycans, kegg_rest=kegg_rest))

def gene_to_compound(add_glycans: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps gene entry IDs (from the KEGG ko database) to related compound IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    gene_to_reaction_: dict = database_link(target_database_name='reaction', source_database_name='ko', kegg_rest=kegg_rest)
    reaction_to_compound_: dict = reaction_to_compound(add_glycans=add_glycans, kegg_rest=kegg_rest)
    gene_to_compound_: dict = {}

    for gene_id, reaction_ids in gene_to_reaction_.items():
        for reaction_id in reaction_ids:
            if reaction_id in reaction_to_compound_.keys():
                compound_ids: set = reaction_to_compound_[reaction_id]
                _add_to_dict(dictionary=gene_to_compound_, key=gene_id, values=compound_ids)

    return gene_to_compound_


def reaction_to_pathway(kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps reaction entry IDs to related pathway IDs.

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=pathway_to_reaction(kegg_rest=kegg_rest))


def pathway_to_reaction(kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps pathway entry IDs to related reaction IDs.

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _pathway_to_database(database='reaction', duplicate_prefix='path:rn', kegg_rest=kegg_rest)


def _pathway_to_database(database: str, duplicate_prefix: str, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps pathway entry IDs to IDs of a given KEGG database.

    :param database: The database with IDs to be mapped to from pathway IDs.
    :param duplicate_prefix: The prefix of duplicate pathway IDs to remove from the mapping.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    pathway_to_database: dict = database_link(target_database_name=database, source_database_name='pathway', kegg_rest=kegg_rest)

    for pathway_id in list(pathway_to_database.keys()):
        if pathway_id.startswith(duplicate_prefix):
            equivalent: str = pathway_id.replace(duplicate_prefix, 'path:map')
            are_equivalent = pathway_to_database[equivalent] == pathway_to_database[pathway_id]

            assert are_equivalent, f'Pathway {equivalent} is not equivalent to {pathway_id}'
            del pathway_to_database[pathway_id]
        else:
            assert pathway_id.startswith('path:map'), f'Unknown path map: {pathway_id}'

    return pathway_to_database


def gene_to_pathway(kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps gene entry IDs (from the KEGG ko database) to related pathway IDs.

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=pathway_to_gene(kegg_rest=kegg_rest))


def pathway_to_gene(kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps pathway entry IDs to related gene IDs (from the KEGG ko database).

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _pathway_to_database(database='ko', duplicate_prefix='path:ko', kegg_rest=kegg_rest)


def reaction_to_gene(kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps reaction entry IDs to related gene IDs (from the KEGG ko database).

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return database_link(target_database_name='ko', source_database_name='reaction', kegg_rest=kegg_rest)


def gene_to_reaction(kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps gene entry IDs (from the KEGG ko database) to related reaction IDs.

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return database_link(target_database_name='reaction', source_database_name='ko', kegg_rest=kegg_rest)
