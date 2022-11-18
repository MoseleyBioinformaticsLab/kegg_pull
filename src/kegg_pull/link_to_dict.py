"""
Creating Dictionaries From KEGG Link Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Contains methods for converting the output from the KEGG "link" REST operation into dictionaries linking the entry IDs from one database to the IDs of related entries.
"""
from . import rest as r

import logging as l
import jsonschema as js
import json as j

class LinkToDict:
    """Class containing methods for creating dictionaries from the output of the "link" KEGG REST operation, both general methods and methods for creating specific mappings."""
    def __init__(self, kegg_rest: r.KEGGrest = None) -> None:
        """
        :param kegg_rest: Optional KEGGrest object for making the "link" operation requests. A new KEGGrest object is created by default.
        """
        self._kegg_rest = kegg_rest if kegg_rest is not None else r.KEGGrest()

    def database_link(self, target_database_name: str, source_database_name: str) -> dict:
        """ Converts the output of the KEGGrest database_link method into a dictionary.

        :param target_database_name: One of the two KEGG databases to pull linked entries from.
        :param source_database_name: The other KEGG database to link entries from the target database.
        :return: The dictionary.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.database_link(
            target_database_name=target_database_name, source_database_name=source_database_name
        )

        return self._to_dict(kegg_response=kegg_response)

    def entries_link(self, target_database_name: str, entry_ids: list) -> dict:
        """ Converts the output of the KEGGrest entries_link method into a dictionary.

        :param target_database_name: The KEGG database to find links to the provided entries.
        :param entry_ids: The IDs of the entries to link to entries in the target database.
        :return: The dictionary.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.entries_link(target_database_name=target_database_name, entry_ids=entry_ids)

        return self._to_dict(kegg_response=kegg_response)

    @staticmethod
    def reverse_mapping(mapping: dict) -> dict:
        """ Reverses the dictionary mapping entry IDs of one database to IDs of related entries, turning keys into values and values into keys.

        :param mapping: The dictionary, of entry IDs (strings) to sets of entry IDs, to reverse.
        :return: The reversed mapping.
        """
        reverse_mapping: dict = {}

        for key, values in mapping.items():
            for value in values:
                LinkToDict._add_to_dict(dictionary=reverse_mapping, key=value, values={key})

        return reverse_mapping

    @staticmethod
    def _to_dict(kegg_response: r.KEGGresponse) -> dict:
        """ Converts output from a "link" KEGG REST operation into a dictionary.

        :param kegg_response: The KEGGresponse object from the "link" operation.
        :return: The dictionary.
        """
        linked_ids = {}

        for link in kegg_response.text_body.strip().split('\n'):
            [link_from_id, link_to_id] = link.split('\t')

            if link_from_id in linked_ids.keys():
                linked_ids[link_from_id].add(link_to_id)
            else:
                linked_ids[link_from_id] = {link_to_id}

        return linked_ids

    def compound_to_pathway(self, add_glycans: bool) -> dict:
        """ Creates a mapping of compound entry IDs to related pathway IDs.

        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        return LinkToDict.reverse_mapping(mapping=self.pathway_to_compound(add_glycans=add_glycans))

    def pathway_to_compound(self, add_glycans: bool) -> dict:
        """ Creates a mapping of pathway entry IDs to related compound IDs.

        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        return self._database_to_compound(database='pathway', add_glycans=add_glycans)

    def _database_to_compound(self, database: str, add_glycans):
        """ Creates a mapping of a given KEGG database to related compound IDs.

        :param database: The database with IDs to map to compound IDs.
        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        database_to_compound: dict = self.database_link(target_database_name='compound', source_database_name=database)

        if add_glycans:
            database_to_glycan: dict = self.database_link(target_database_name='glycan', source_database_name=database)
            glycan_to_compound: dict = self.database_link(target_database_name='compound', source_database_name='glycan')

            for entry_id, glycan_ids in database_to_glycan.items():
                for glycan_id in glycan_ids:
                    if glycan_id in glycan_to_compound.keys():
                        glycan_compound_ids: set = glycan_to_compound[glycan_id]
                        LinkToDict._add_to_dict(dictionary=database_to_compound, key=entry_id, values=glycan_compound_ids)

        return database_to_compound

    @staticmethod
    def _add_to_dict(dictionary: dict, key: str, values: set) -> None:
        """ Adds a set of values to a set mapped from a given key in a dictionary.

        :param dictionary: The dictionary mapping to sets, one of which the value will be added to.
        :param key: The key in the dictionary mapping to the set that the values will be added to.
        :param values: The values to add to the set mapped to by the key.
        """
        if key in dictionary.keys():
            dictionary[key].update(values)
        else:
            dictionary[key] = values

    def compound_to_reaction(self, add_glycans: bool) -> dict:
        """ Creates a mapping of compound entry IDs to related reaction IDs.

        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        return LinkToDict.reverse_mapping(mapping=self.reaction_to_compound(add_glycans=add_glycans))

    def reaction_to_compound(self, add_glycans: bool) -> dict:
        """ Creates a mapping of reaction entry IDs to related compound IDs.

        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        return self._database_to_compound(database='reaction', add_glycans=add_glycans)

    def compound_to_gene(self, add_glycans: bool) -> dict:
        """ Creates a mapping of compound entry IDs to related gene IDs (from the KEGG ko database).

        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        return LinkToDict.reverse_mapping(mapping=self.gene_to_compound(add_glycans=add_glycans))

    def gene_to_compound(self, add_glycans: bool) -> dict:
        """ Creates a mapping of gene entry IDs (from the KEGG ko database) to related compound IDs.

        :param add_glycans: Whether to add the corresponding compound IDs of KEGG glycan entries.
        :return: The mapping.
        """
        gene_to_reaction: dict = self.database_link(target_database_name='reaction', source_database_name='ko')
        reaction_to_compound: dict = self.reaction_to_compound(add_glycans=add_glycans)
        gene_to_compound: dict = {}

        for gene_id, reaction_ids in gene_to_reaction.items():
            for reaction_id in reaction_ids:
                if reaction_id in reaction_to_compound.keys():
                    compound_ids: set = reaction_to_compound[reaction_id]
                    LinkToDict._add_to_dict(dictionary=gene_to_compound, key=gene_id, values=compound_ids)

        return gene_to_compound

    def reaction_to_pathway(self) -> dict:
        """ Creates a mapping of reaction entry IDs to related pathway IDs.

        :return: The mapping.
        """
        return LinkToDict.reverse_mapping(mapping=self.pathway_to_reaction())

    def pathway_to_reaction(self) -> dict:
        """ Creates a mapping of pathway entry IDs to related reaction IDs.

        :return: The mapping.
        """
        return self._pathway_to_database(database='reaction', duplicate_prefix='path:rn')

    def _pathway_to_database(self, database: str, duplicate_prefix: str) -> dict:
        """ Creates a mapping of a pathway entry IDs to a IDs of a given KEGG database.

        :param database: The database with IDs to be mapped to from pathway IDs.
        :param duplicate_prefix: The prefix of duplicate pathway IDs to remove from the mapping.
        :return: The mapping.
        """
        pathway_to_database: dict = self.database_link(target_database_name=database, source_database_name='pathway')

        for pathway_id in list(pathway_to_database.keys()):
            if pathway_id.startswith(duplicate_prefix):
                equivalent: str = pathway_id.replace(duplicate_prefix, 'path:map')
                are_equivalent = pathway_to_database[equivalent] == pathway_to_database[pathway_id]

                assert are_equivalent, f'Pathway {equivalent} is not equivalent to {pathway_id}'
                del pathway_to_database[pathway_id]
            else:
                assert pathway_id.startswith('path:map'), f'Unknown path map: {pathway_id}'

        return pathway_to_database

    def gene_to_pathway(self) -> dict:
        """ Creates a mapping of gene entry IDs (from the KEGG ko database) to related pathway IDs.

        :return: The mapping.
        """
        return LinkToDict.reverse_mapping(mapping=self.pathway_to_gene())

    def pathway_to_gene(self) -> dict:
        """ Creates a mapping of pathway entry IDs to related gene IDs (from the KEGG ko database).

        :return: The mapping.
        """
        return self._pathway_to_database(database='ko', duplicate_prefix='path:ko')

    def reaction_to_gene(self) -> dict:
        """ Creates a mapping of reaction entry IDs to related gene IDs (from the KEGG ko database).

        :return: The mapping.
        """
        return self.database_link(target_database_name='ko', source_database_name='reaction')

    def gene_to_reaction(self) -> dict:
        """ Creates a mapping of gene entry IDs (from the KEGG ko database) to related reaction IDs.

        :return: The mapping.
        """
        return self.database_link(target_database_name='reaction', source_database_name='ko')

    @staticmethod
    def save_json(mapping: dict, file_path: str) -> None:
        """ Saves a KEGG mapping to a JSON file.

        :param mapping: The mapping of KEGG entry IDs to sets of IDs.
        :param file_path: The path to the JSON file.
        :raises ValidationError: Raised if the mapping does not follow the correct JSON schema.
        """
        for entry_id, entry_ids in mapping.items():
            mapping[entry_id] = sorted(entry_ids)

        LinkToDict._validate_json(mapping=mapping)

        with open(file_path, 'w') as file:
            j.dump(mapping, file)

    @staticmethod
    def _validate_json(mapping: dict) -> None:
        """ Ensures a mapping follows the correct schema.

        :param mapping: The mapping to validate.
        :raises ValueError: Raised if the mapping does not follow the correct JSON schema.
        """
        mapping_schema = {
            'type': 'object',
            'patternProperties': {
                '^.*$': {
                    'type': 'array',
                    'items': {
                        'type': 'string'
                    }
                }
            }
        }

        try:
            js.validate(instance=mapping, schema=mapping_schema)
        except js.exceptions.ValidationError as e:
            l.error('The mapping must be a dictionary of KEGG entry IDs (strings) mapped to a set of KEGG entry IDs')

            raise e

    @staticmethod
    def load_json(file_path: str) -> dict:
        """ Loads a KEGG mapping from a JSON file.

        :param file_path: The path to the JSON file.
        :return: The mapping.
        :raises ValidationError: Raised if the JSON file does not follow the correct schema.
        """
        with open(file_path, 'r') as file:
            mapping: dict = j.load(file)

        LinkToDict._validate_json(mapping=mapping)

        for entry_id, entry_ids in mapping.items():
            mapping[entry_id] = set(entry_ids)

        return mapping
