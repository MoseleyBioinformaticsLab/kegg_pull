"""
Creating Dictionaries From KEGG Link Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Contains methods for converting the output from the KEGG "link" REST operation into dictionaries linking the entry IDs from one database to the IDs of related entries.
"""

from . import rest as r

class LinkToDict:
    """
    Class containing methods for creating dictionaries from the output of the "link" KEGG REST operation.
    """
    def __init__(self, kegg_rest: r.KEGGrest = None) -> None:
        """
        :param kegg_rest: Optional kegg_rest object for making the "link" operation requests. One is created by default.
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
        return LinkToDict.reverse_mapping(mapping=self.pathway_to_compound(add_glycans=add_glycans))

    def pathway_to_compound(self, add_glycans: bool) -> dict:
        return self._database_to_compound(database='pathway', add_glycans=add_glycans)

    def _database_to_compound(self, database: str, add_glycans):
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
        if key in dictionary.keys():
            dictionary[key].update(values)
        else:
            dictionary[key] = values

    def compound_to_reaction(self, add_glycans: bool) -> dict:
        return LinkToDict.reverse_mapping(mapping=self.reaction_to_compound(add_glycans=add_glycans))

    def reaction_to_compound(self, add_glycans: bool) -> dict:
        return self._database_to_compound(database='reaction', add_glycans=add_glycans)

    def compound_to_gene(self, add_glycans: bool) -> dict:
        return LinkToDict.reverse_mapping(mapping=self.gene_to_compound(add_glycans=add_glycans))

    def gene_to_compound(self, add_glycans: bool) -> dict:
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
        return LinkToDict.reverse_mapping(mapping=self.pathway_to_reaction())

    def pathway_to_reaction(self) -> dict:
        return self._pathway_to_database(database='reaction', duplicate_prefix='path:rn')

    def _pathway_to_database(self, database: str, duplicate_prefix: str) -> dict:
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
        return LinkToDict.reverse_mapping(mapping=self.pathway_to_gene())

    def pathway_to_gene(self) -> dict:
        return self._pathway_to_database(database='ko', duplicate_prefix='path:ko')

    def reaction_to_gene(self) -> dict:
        return self.database_link(target_database_name='ko', source_database_name='reaction')

    def gene_to_reaction(self) -> dict:
        return self.database_link(target_database_name='reaction', source_database_name='ko')
