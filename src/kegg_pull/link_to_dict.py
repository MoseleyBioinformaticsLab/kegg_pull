"""
Creating Dictionaries From KEGG Link Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Functionality for converting the output from the KEGG "link" REST operation into dictionaries linking the entry IDs from one database to the IDs of related entries.
"""
import typing as t
import json as j

from . import rest as r
from . import kegg_url as ku
from . import _utils as u


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
        [link_from_id, link_to_id] = link.strip().split('\t')

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


def compound_to_pathway(add_glycans: bool, add_drugs: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps compound entry IDs to related pathway IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=pathway_to_compound(add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest))


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


def pathway_to_compound(add_glycans: bool, add_drugs: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps pathway entry IDs to related compound IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _database_to_compound(database='pathway', add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest)


def _database_to_compound(database: str, add_glycans: bool, add_drugs: bool, kegg_rest: t.Union[r.KEGGrest, None]) -> dict:
    """ Creates a dictionary that maps the entry IDs of a given KEGG database to related compound IDs.

    :param database: The database with IDs to map to compound IDs.
    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    database_to_compound: dict = database_link(target_database_name='compound', source_database_name=database, kegg_rest=kegg_rest)

    def add_compound_database(compound_database: str) -> None:
        database_to_compound_database: dict = database_link(
            target_database_name=compound_database, source_database_name=database, kegg_rest=kegg_rest
        )

        compound_database_to_compound: dict = database_link(
            target_database_name='compound', source_database_name=compound_database, kegg_rest=kegg_rest
        )

        _add_indirect_mappings(
            database1_to_database3=database_to_compound, database1_to_database2=database_to_compound_database,
            database2_to_database3=compound_database_to_compound
        )

    if add_glycans:
        add_compound_database(compound_database='glycan')

    if add_drugs:
        add_compound_database(compound_database='drug')

    return database_to_compound


def _add_indirect_mappings(database1_to_database3: dict, database1_to_database2: dict, database2_to_database3: dict) -> None:
    """ Adds indirect mappings to a dictionary using an intermediary dictionary.

    :param database1_to_database3: The dictionary to add indirect mappings to.
    :param database1_to_database2: The intermediary dictionary.
    :param database2_to_database3: The dictionary with mapped values to add.
    """
    for entry_id1, entry_ids2 in database1_to_database2.items():
        for entry_id2 in entry_ids2:
            if entry_id2 in database2_to_database3.keys():
                entry_ids3: set = database2_to_database3[entry_id2]
                _add_to_dict(dictionary=database1_to_database3, key=entry_id1, values=entry_ids3)


def compound_to_reaction(add_glycans: bool, add_drugs: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps compound entry IDs to related reaction IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=reaction_to_compound(add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest))


def reaction_to_compound(add_glycans: bool, add_drugs: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps reaction entry IDs to related compound IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _database_to_compound(database='reaction', add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest)

def compound_to_gene(add_glycans: bool, add_drugs: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps compound entry IDs to related gene IDs (from the KEGG ko database).

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return reverse_mapping(mapping=gene_to_compound(add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest))

def gene_to_compound(add_glycans: bool, add_drugs: bool, kegg_rest: r.KEGGrest = None) -> dict:
    """ Creates a dictionary that maps gene entry IDs (from the KEGG ko database) to related compound IDs.

    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    gene_to_reaction_: dict = database_link(target_database_name='reaction', source_database_name='ko', kegg_rest=kegg_rest)
    reaction_to_compound_: dict = reaction_to_compound(add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest)
    gene_to_compound_: dict = {}

    _add_indirect_mappings(
        database1_to_database3=gene_to_compound_, database1_to_database2=gene_to_reaction_,
        database2_to_database3=reaction_to_compound_
    )

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


_mapping_schema = {
    'type': 'object',
    'minProperties': 1,
    'additionalProperties': False,
    'patternProperties': {
        '^.+$': {
            'type': 'array',
            'minItems': 1,
            'items': {
                'type': 'string',
                'minLength': 1
            }
        }
    }
}


_validation_error_message = 'The mapping must be a dictionary of KEGG entry IDs (strings) mapped to a set of KEGG entry IDs'


def to_json_string(mapping: dict) -> str:
    """ Converts a mapping of linked KEGG entry IDs (dictionary created with this link_to_dict module) to a JSON string.

    :param mapping: The dictionary to convert.
    :return: The JSON string.
    :raises ValidationError: Raised if the mapping does not follow the correct JSON schema. Should follow the correct schema if the dictionary was created with this link_to_dict module.
    """
    mapping_to_convert = {}

    for entry_id, entry_ids in mapping.items():
        mapping_to_convert[entry_id] = sorted(entry_ids)

    u.validate_json_object(
        json_object=mapping_to_convert, json_schema=_mapping_schema, validation_error_message=_validation_error_message
    )

    return j.dumps(mapping_to_convert, indent=2)


def save_to_json(mapping: dict, file_path: str) -> None:
    """ Saves a mapping of linked KEGG entry IDs (dictionary created with this link_to_dict module) to a JSON file, either in a
    regular directory or ZIP archive.

    :param mapping: The mapping to save.
    :param file_path: The path to the JSON file. If in a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
    :raises ValidationError: Raised if the mapping does not follow the correct JSON schema. Should follow the correct schema if the dictionary was created with this link_to_dict module.
    """
    mapping: str = to_json_string(mapping=mapping)
    u.save_output(output_target=file_path, output_content=mapping)


def load_from_json(file_path: str) -> dict:
    """ Loads a mapping of linked KEGG entry IDs (dictionary created with this link_to_dict module) to a JSON file, either in a
    regular directory or ZIP archive.

    :param file_path: The path to the JSON file. If in a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
    :return: The mapping.
    :raises ValidationError: Raised if the mapping does not follow the correct JSON schema. Should follow the correct schema if the dictionary was created with this link_to_dict module.
    """
    mapping: dict = u.load_json_file(file_path=file_path, json_schema=_mapping_schema, validation_error_message=_validation_error_message)

    for entry_id, entry_ids in mapping.items():
        mapping[entry_id] = set(entry_ids)

    return mapping
