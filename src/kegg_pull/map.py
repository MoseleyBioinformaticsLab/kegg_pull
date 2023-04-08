"""
Constructing Mappings From KEGG "link" And "conv" Operations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|Functionality| for converting the output from the KEGG "link" or "conv" REST operations into mappings of the entry IDs from one database to the IDs of related entries.
"""
import typing as t
import json
import copy as cp
import logging as log
from . import rest as r
from . import kegg_url as ku
from . import _utils as u

KEGGmapping = dict[str, set[str]]


def database_link(
        source_database: str, target_database: str, deduplicate: bool = False, add_glycans: bool = False,
        add_drugs: bool = False, kegg_rest: r.KEGGrest | None = None) -> KEGGmapping:
    """ Converts the output of the KEGG "link" operation (of the form that maps the entry IDs of one database to the entry IDs of another) into a dictionary along with other helpful optional functionality.

    :param source_database: The name of the database with entry IDs mapped to the target database.
    :param target_database: The name of the database with entry IDs mapped from the source database.
    :param deduplicate: Some mappings including "pathway" entry IDs result in half beginning with the normal "path:map" prefix but the other half with a different prefix. If True, removes the IDs corresponding to entries that are identical but with a different prefix.
    :param add_glycans: Whether to add the corresponding compound IDs of equivalent glycan entries. Logs a warning if neither the source nor the target database is "compound".
    :param add_drugs: Whether to add the corresponding compound IDs of equivalent drug entries. Logs a warning if neither the source nor the target database is "compound".
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default  parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    :raises ValueError: Raised if deduplicate is True but neither source_database nor target_database is "pathway".
    """
    mapping = _to_dict(
        kegg_rest=kegg_rest, KEGGurl=ku.DatabaseLinkKEGGurl, target_database=target_database,
        source_database=source_database)
    mapping = _deduplicate_pathway_ids(
        mapping=mapping, deduplicate=deduplicate, source_database=source_database,
        target_database=target_database)
    mapping = _add_glycans_or_drugs(
        mapping=mapping, source_database=source_database, target_database=target_database,
        add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest)
    return mapping


def _to_dict(kegg_rest: r.KEGGrest | None, KEGGurl: type[ku.AbstractKEGGurl], **kwargs) -> KEGGmapping:
    """ Converts output from the KEGG "link" operation into a dictionary.

    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :param KEGGurl: The class extending AbstractKEGGurl used to form the URL for the "link" operation.
    :param kwargs: The keyword arguments for constructing the URL.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    kegg_response = r.request_and_check_error(kegg_rest=kegg_rest, KEGGurl=KEGGurl, **kwargs)
    text_body = kegg_response.text_body.strip()
    mapped_ids = KEGGmapping()
    # If a non-empty response was provided, fill in the mapping with the data
    if text_body:
        for one_to_one in text_body.split('\n'):
            [map_from_id, map_to_id] = one_to_one.strip().split('\t')
            _add_to_dict(dictionary=mapped_ids, key=map_from_id, values={map_to_id})
    return mapped_ids


def _add_to_dict(dictionary: KEGGmapping, key: str, values: set[str]) -> None:
    """ Adds a set of values to a set mapped from a given key in a dictionary.

    :param dictionary: The dictionary mapping to sets, one of which the values will be added to.
    :param key: The key in the dictionary mapping to the set that the values will be added to.
    :param values: The values to add to the set mapped to by the key.
    """
    if key in dictionary.keys():
        dictionary[key].update(values)
    else:
        dictionary[key] = cp.deepcopy(values)  # In case "values" is referenced elsewhere, we don't want to update a shallow copy


def _deduplicate_pathway_ids(mapping: KEGGmapping, deduplicate: bool, source_database: str, target_database: str) -> KEGGmapping:
    """ If requested, removes entry IDs corresponding to duplicate pathway map entries (different ID, same entry).

    :param mapping: The mapping to deduplicate.
    :param deduplicate: Whether or not to deduplicate.
    :param source_database: The name of the source database of the mapping to validate.
    :param target_database: The name of the target database of the mapping to validate.
    :raises ValueError: Raised if deduplicate is True but neither source_database nor target_database is "pathway".
    """
    if deduplicate:
        if source_database != 'pathway' and target_database != 'pathway':
            raise ValueError(
                f'Cannot deduplicate path:map entry ids when neither the source database nor the target database is set to '
                f'"pathway". Databases specified: {source_database}, {target_database}.')

        # noinspection PyShadowingNames
        def deduplicate_pathway_ids(mapping: KEGGmapping, **_) -> KEGGmapping:
            for pathway_id in list(mapping.keys()):
                if not pathway_id.startswith('path:map'):
                    del mapping[pathway_id]
            return mapping
        mapping = _process_mapping(
            mapping=mapping, func=deduplicate_pathway_ids, source_database=source_database,
            target_database=target_database, relevant_database='pathway')
    return mapping


def _process_mapping(
        mapping: KEGGmapping, func: t.Callable[..., KEGGmapping], source_database: str, target_database: str, relevant_database: str) -> KEGGmapping:
    """ Performs additional processing on a mapping according to a provided function.

    :param mapping: The mapping to process.
    :param func: The function that processes the mapping.
    :param source_database: The name of the source database of the mapping.
    :param target_database: The name of the target database of the mapping.
    :param relevant_database: The name of the database (expected to be either the source or the target) to which the processing is relevant.
    :return: The processed mapping.
    """
    double_reverse = target_database == relevant_database
    if double_reverse:
        mapping = _reverse(mapping=mapping)
        target_database = source_database
    mapping = func(mapping=mapping, target_database=target_database)
    if double_reverse:
        mapping = _reverse(mapping=mapping)
    return mapping


def _add_glycans_or_drugs(
        mapping: KEGGmapping, source_database: str, target_database: str, add_glycans: bool, add_drugs: bool,
        kegg_rest: r.KEGGrest | None = None) -> KEGGmapping:
    """ If requested, adds the corresponding compound IDs of equivalent glycan and/or drug entries to a mapping (assuming mapping from "compound" to some target database).

    :param mapping: The mapping to add the IDs of compound-equivalents which cross-reference the target database.
    :param source_database: Logs a warning if not equal to "compound" and if the target database name is also not equal to "compound".
    :param target_database: The database with IDs to which compound IDs are mapped.
    :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
    :param add_drugs: Whether to add the corresponding compound IDs of KEGG drug entries.
    :param kegg_rest: The KEGGrest object to perform the "link" operation(s). If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    if add_glycans or add_drugs:
        if source_database != 'compound' and target_database != 'compound':
            log.warning(
                f'Adding compound IDs (corresponding to equivalent glycan and/or drug entries) to a mapping where neither the source'
                f' database nor the target database are "compound". Databases specified: {source_database}, '
                f'{target_database}.')

        # noinspection PyShadowingNames
        def add_glycans_or_drugs(mapping: KEGGmapping, target_database: str) -> KEGGmapping:
            if add_glycans:
                glycan_to_database = indirect_link(
                    source_database='compound', intermediate_database='glycan', target_database=target_database,
                    kegg_rest=kegg_rest)
                mapping = combine_mappings(mapping1=mapping, mapping2=glycan_to_database)
            if add_drugs:
                drug_to_database = indirect_link(
                    source_database='compound', intermediate_database='drug', target_database=target_database,
                    kegg_rest=kegg_rest)
                mapping = combine_mappings(mapping1=mapping, mapping2=drug_to_database)
            return mapping
        mapping = _process_mapping(
            mapping=mapping, func=add_glycans_or_drugs, source_database=source_database,
            target_database=target_database, relevant_database='compound')
    return mapping


# noinspection PyShadowingNames
def database_conv(
        kegg_database: str, outside_database: str, reverse: bool = False, kegg_rest: r.KEGGrest | None = None) -> KEGGmapping:
    """ Converts the output of the KEGG "conv" operation (of the form that maps the entry IDs of one database to the entry IDs of another) into a dictionary.

    :param kegg_database: The name of the KEGG database with entry IDs mapped to the outside database.
    :param outside_database: The name of the outside database with entry IDs mapped from the KEGG database.
    :param reverse: Reverses the mapping with the target becoming the source and the source becoming the target. Equivalent to calling the reverse() function of this module.
    :param kegg_rest: The KEGGrest object to perform the "conv" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _map_and_reverse(
        reverse=reverse, kegg_rest=kegg_rest, KEGGurl=ku.DatabaseConvKEGGurl, kegg_database=kegg_database,
        outside_database=outside_database)


# noinspection PyShadowingNames
def _map_and_reverse(reverse: bool, **kwargs) -> KEGGmapping:
    """ Helper function for general mapping functionality ("link" or "conv") that creates a mapping with the option to reverse.

    :param reverse: Reverses the mapping with the target becoming the source and the source becoming the target.
    :param kwargs: The arguments for the _to_dict helper method.
    :return:
    """
    mapping = _to_dict(**kwargs)
    if reverse:
        mapping = _reverse(mapping=mapping)
    return mapping


# noinspection PyShadowingNames
def entries_link(
        entry_ids: list[str], target_database: str, reverse: bool = False,
        kegg_rest: r.KEGGrest | None = None) -> KEGGmapping:
    """ Converts the output of the KEGG "link" operation (of the form that maps specific provided entry IDs to the IDs of a target database) to a dictionary.

    :param entry_ids: The IDs of the entries to map to entries in the target database.
    :param target_database: The name of the database with entry IDs mapped to from the provided entry IDs.
    :param reverse: Reverses the mapping with the target becoming the source and the source becoming the target. Equivalent to calling the reverse() function of this module.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _map_and_reverse(
        reverse=reverse, kegg_rest=kegg_rest, KEGGurl=ku.EntriesLinkKEGGurl, target_database=target_database, entry_ids=entry_ids)


# noinspection PyShadowingNames
def entries_conv(
        entry_ids: list[str], target_database: str, reverse: bool = False, kegg_rest: r.KEGGrest | None = None) -> KEGGmapping:
    """ Converts the output of the KEGG "conv" operation (of the form that maps specific provided entry IDs to the IDs of a target database) to a dictionary.

    :param entry_ids: The IDs of the entries to map to entries in the target database.
    :param target_database: The name of the database with entry IDs mapped to from the provided entry IDs.
    :param reverse: Reverses the mapping with the target becoming the source and the source becoming the target. Equivalent to calling the reverse() function of this module.
    :param kegg_rest: The KEGGrest object to perform the "link" operation. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    """
    return _map_and_reverse(
        reverse=reverse, kegg_rest=kegg_rest, KEGGurl=ku.EntriesConvKEGGurl, target_database=target_database, entry_ids=entry_ids)


def indirect_link(
        source_database: str, intermediate_database: str, target_database: str, deduplicate: bool = False,
        add_glycans: bool = False, add_drugs: bool = False, kegg_rest: r.KEGGrest | None = None) -> KEGGmapping:
    """ Creates a dictionary that maps the entry IDs of a source database to those of a target database using an intermediate database ("link" operation) e.g. ko-to-compound where the intermediate is reaction (connecting cross-references of ko-to-reaction and reaction-to-compound).

    :param source_database: The name of the database with entry IDs to map to the target database.
    :param intermediate_database: The name of the database with which two mappings are made i.e. source-to-intermediate and intermediate-to-target, both of which are merged to create source-to-target.
    :param target_database: The name of the database with entry IDs to which those of the source database are mapped.
    :param deduplicate: Some mappings including "pathway" entry IDs result in half beginning with the normal "path:map" prefix but the other half with a different prefix. If True, removes the IDs corresponding to entries that are identical but with a different prefix.
    :param add_glycans: Whether to add the corresponding compound IDs of equivalent glycan entries. Logs a warning if neither the source nor the target database are "compound".
    :param add_drugs: Whether to add the corresponding compound IDs of equivalent drug entries. Logs a warning if neither the source nor the target database are "compound".
    :param kegg_rest: The KEGGrest object to perform the "link" operations. If None, one is created with the default parameters.
    :return: The dictionary.
    :raises RuntimeError: Raised if the request to the KEGG REST API fails or times out.
    :raises ValueError: Raised if deduplicate is True but neither source_database nor target_database is "pathway".
    """
    if len({source_database, intermediate_database, target_database}) < 3:
        raise ValueError(
            f'The source, intermediate, and target database must all be unique. Databases specified: {source_database}, '
            f'{intermediate_database}, {target_database}.')
    source_to_target = KEGGmapping()
    source_to_intermediate = _to_dict(
        kegg_rest=kegg_rest, KEGGurl=ku.DatabaseLinkKEGGurl, source_database=source_database,
        target_database=intermediate_database)
    intermediate_to_target = _to_dict(
        kegg_rest=kegg_rest, KEGGurl=ku.DatabaseLinkKEGGurl, source_database=intermediate_database,
        target_database=target_database)
    for source_id, intermediate_ids in source_to_intermediate.items():
        for intermediate_id in intermediate_ids:
            if intermediate_id in intermediate_to_target.keys():
                target_ids = intermediate_to_target[intermediate_id]
                _add_to_dict(dictionary=source_to_target, key=source_id, values=target_ids)
    source_to_target = _deduplicate_pathway_ids(
        mapping=source_to_target, deduplicate=deduplicate, source_database=source_database,
        target_database=target_database)
    source_to_target = _add_glycans_or_drugs(
        mapping=source_to_target, source_database=source_database, target_database=target_database,
        add_glycans=add_glycans, add_drugs=add_drugs, kegg_rest=kegg_rest)
    return source_to_target


def combine_mappings(mapping1: KEGGmapping, mapping2: KEGGmapping) -> KEGGmapping:
    """ Combines two mappings together. If a key in mapping 2 is already in mapping 1, their values are merged in the combined mapping e.g. X -> {A,B} and X -> {B,C} becomes X -> {A,B,C}.

    :param mapping1: The first mapping to combine.
    :param mapping2: The second mapping to combine.
    :return: The combined mapping.
    """
    combined = dict()
    for key1, values1 in mapping1.items():
        _add_to_dict(dictionary=combined, key=key1, values=values1)
    for key2, values2 in mapping2.items():
        _add_to_dict(dictionary=combined, key=key2, values=values2)
    return combined


def reverse(mapping: KEGGmapping) -> KEGGmapping:
    """ Reverses the dictionary (mapping entry IDs of one database to IDs of related entries) turning keys into values and values into keys.

    :param mapping: The dictionary (of entry IDs (strings) to sets of entry IDs) to reverse.
    :return: The reversed mapping.
    """
    reversed_mapping = dict()
    for key, values in mapping.items():
        for value in values:
            _add_to_dict(dictionary=reversed_mapping, key=value, values={key})
    return reversed_mapping


_reverse = reverse  # So functions can have a "reverse" boolean parameter without overriding the module-level "reverse" function.
_mapping_schema = {
    'type': 'object',
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
_validation_error_message = 'The mapping must be a dictionary of entry IDs (strings) mapped to a set of entry IDs'


def to_json_string(mapping: KEGGmapping) -> str:
    """ Converts a mapping of entry IDs (dictionary created with this map module) to a JSON string.

    :param mapping: The dictionary to convert.
    :return: The JSON string.
    :raises ValidationError: Raised if the mapping does not follow the correct JSON schema. Should follow the correct schema if the dictionary was created with this map module.
    """
    mapping_to_convert = dict[str, list[str]]()
    for entry_id, entry_ids in mapping.items():
        mapping_to_convert[entry_id] = sorted(entry_ids)
    u.validate_json_object(
        json_object=mapping_to_convert, json_schema=_mapping_schema, validation_error_message=_validation_error_message)
    return json.dumps(mapping_to_convert, indent=2)


def save_to_json(mapping: KEGGmapping, file_path: str) -> None:
    """ Saves a mapping of entry IDs (dictionary created with this map module) to a JSON file, either in a
    regular directory or ZIP archive.

    :param mapping: The mapping to save.
    :param file_path: The path to the JSON file. If in a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
    :raises ValidationError: Raised if the mapping does not follow the correct JSON schema. Should follow the correct schema if the dictionary was created with this map module.
    """
    mapping_str: str = to_json_string(mapping=mapping)
    u.save_output(output_target=file_path, output_content=mapping_str)


def load_from_json(file_path: str) -> KEGGmapping:
    """ Loads a mapping of entry IDs (dictionary created with this map module) to a JSON file, either in a
    regular directory or ZIP archive.

    :param file_path: The path to the JSON file. If in a ZIP archive, the file path must be in the following format: /path/to/zip-archive.zip:/path/to/file (e.g. ./archive.zip:mapping.json).
    :return: The mapping.
    :raises ValidationError: Raised if the mapping does not follow the correct JSON schema. Should follow the correct schema if the dictionary was created with this map module.
    """
    mapping: KEGGmapping = u.load_json_file(file_path=file_path, json_schema=_mapping_schema, validation_error_message=_validation_error_message)
    for entry_id, entry_ids in mapping.items():
        mapping[entry_id] = set(entry_ids)
    return mapping
