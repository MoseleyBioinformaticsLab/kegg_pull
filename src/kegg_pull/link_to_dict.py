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
        """ Converts the output od the KEGGrest database_link method into a dictionary.

        :param target_database_name: One of the two KEGG databases to pull linked entries from.
        :param source_database_name: The other KEGG database to link entries from the target database.
        :return: The dictionary.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.database_link(
            target_database_name=target_database_name, source_database_name=source_database_name
        )

        return self._to_dict(kegg_response=kegg_response)

    def entries_link(self, target_database_name: str, entry_ids: list) -> dict:
        """ Converts the output od the KEGGrest entries_link method into a dictionary.

        :param target_database_name: The KEGG database to find links to the provided entries.
        :param entry_ids: The IDs of the entries to link to entries in the target database.
        :return: The dictionary.
        """
        kegg_response: r.KEGGresponse = self._kegg_rest.entries_link(target_database_name=target_database_name, entry_ids=entry_ids)

        return self._to_dict(kegg_response=kegg_response)

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
