"""
Classes for creating KEGG REST API URLs for both the list and get API operations.
"""
import logging
import abc
import typing as t

BASE_URL: str = 'https://rest.kegg.jp'


class AbstractKEGGurl(abc.ABC):
    """
    Abstract class containing the base data and functionality for all KEGG URL classes which validate and construct URLs
    for accessing the KEGG web API.
    """
    def __init__(self, api_operation: str, base_url: str = BASE_URL, **kwargs):
        """ Validates the arguments and constructs the KEGG API URL from them.

        :param api_operation: The KEGG API operation in the URL
        :param base_url: The base URL for accessing the KEGG web API
        :param kwargs: The arguments used to construct the URL options after they are validated
        """
        self._validate(**kwargs)
        url_options: str = self._create_rest_options(**kwargs)
        self._url = f'{base_url}/{api_operation}/{url_options}'

    @abc.abstractmethod
    def _validate(self, **kwargs):
        """ Ensures the arguments passed into the constructor result in a valid KEGG URL.

        :param kwargs: The arguments to validate
        :raises ValueError:
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _create_rest_options(self, **kwargs) -> str:
        """ Creates the string at the end part of a KEGG URL to specify the options for a REST API request.

        :param kwargs: The arguments used to create the options
        :return: The REST API options
        """
        pass  # pragma: no cover

    @property
    @abc.abstractmethod
    def _valid_rest_options(self) -> t.Iterable:
        """Property containing the collection of valid KEGG REST API options for a given operation."""
        pass

    @property
    def url(self) -> str:
        return self._url

    def __repr__(self):
        return self.url

    @staticmethod
    def _raise_error(reason: str):
        """ Raises an exception for when a URL is not valid.

        :param reason: The reason why the URL was not valid
        :raises ValueError:
        """
        raise ValueError(f'Cannot create URL - {reason}')

    def _validate_rest_option(self, option_name: str, option_value: str):
        """ Raises an exception if a provided REST API option is not valid.

        :param option_name: The name of the type of option to check
        :param option_value: The value of the REST API option provided
        :raises ValueError:
        """
        if option_value not in self._valid_rest_options:
            valid_options = ', '.join(sorted(self._valid_rest_options))
            self._raise_error(reason=f'Invalid {option_name}: "{option_value}". Valid values are: {valid_options}')


class ListKEGGurl(AbstractKEGGurl):
    """Contains the validation implementation and construction of the KEGG API list operation."""
    def __init__(self, database_type: str):
        """ Validates and constructs a KEGG URL for the list API operation.

        :param database_type: The database option for the KEGG list URL
        """
        super().__init__(api_operation='list', database_type=database_type)

    def _validate(self, database_type: str):
        """ Ensures the database provided is a valid KEGG database.

        :param database_type: The name of the database to validate
        """
        self._validate_rest_option(option_name='database type', option_value=database_type)

    def _create_rest_options(self, database_type: str) -> str:
        """ Implements the KEGG REST API options creation by returning the provided database. That's the only option for
        the list operation.

        :param database_type: The database option
        :return: The database option
        """
        return database_type

    def _valid_rest_options(self) -> t.Iterable:
        """Returns the collection of valid databases for the list operation."""
        return {
        'pathway', 'brite', 'module', 'ko', 'genome', 'vg', 'vp', 'ag', 'compound', 'glycan', 'reaction', 'rclass',
        'enzyme', 'network', 'variant', 'disease', 'drug', 'dgroup'
    }


class GetKEGGurl(AbstractKEGGurl):
    """Contains validation and URL construction as well as a helpful interface for the KEGG API get operation."""
    _entry_fields = {
        'aaseq': True, 'ntseq': True, 'mol': True, 'kcf': True, 'image': False, 'conf': False, 'kgml': False,
        'json': False
    }

    def __init__(self, entry_ids: list, entry_field: str = None):
        """ Validates and constructs the entry IDs and entry field options.

        :param entry_ids: Specifies which entry IDs go in the first option of the URL
        :param entry_field: Specifies which entry field goes in the second option
        """
        super().__init__(api_operation='get', entry_ids=entry_ids, entry_field=entry_field)
        self._entry_ids = entry_ids
        self._entry_field = entry_field

    @property
    def entry_ids(self) -> list:
        return self._entry_ids

    @property
    def multiple_entry_ids(self) -> bool:
        return len(self.entry_ids) > 1

    def _validate(self, entry_ids: list, entry_field: str):
        """ Ensures valid Entry IDs and a valid entry field are provided.

        :param entry_ids: The entry IDs to validate
        :param entry_field: The entry field to validate
        """
        n_entry_ids: int = len(entry_ids)

        if n_entry_ids == 0:
            self._raise_error(reason='Entry IDs must be specified for the KEGG get operation')

        if entry_field is not None:
            self._validate_rest_option(option_name='KEGG entry field', option_value=entry_field)

            if self.only_one_entry(entry_field=entry_field) and n_entry_ids > 1:
                self._raise_error(
                    reason=f'The KEGG entry field: "{entry_field}" only supports requests of one KEGG entry '
                           f'at a time but {n_entry_ids} entry IDs are provided'
                )

    def _valid_rest_options(self) -> t.Iterable:
        """Returns the collection of valid entry fields for the get API operation."""
        return self._entry_fields

    @staticmethod
    def only_one_entry(entry_field: str) -> bool:
        """ Determines whether a KEGG entry field can only be pulled in one entry at a time for the KEGG get API
        operation.

        :param entry_field: The KEGG entry field to check
        """
        return entry_field is not None and not GetKEGGurl._entry_fields[entry_field]

    def _create_rest_options(self, entry_ids: list, entry_field: str) -> str:
        """ Constructs the URL options for the KEGG API get operation.

        :param entry_ids: The entry IDs for the first URL option
        :param entry_field: The entry field for the second URL option
        :return: The constructed options
        """
        entry_ids_url_option = '+'.join(entry_ids)

        if entry_field is not None:
            return f'{entry_ids_url_option}/{entry_field}'
        else:
            return entry_ids_url_option

    def split_entries(self):
        """ Converts a KEGG get URL with multiple entry IDs into separate URLs each with one entry ID. Logs a warning if
        the initial URL only has one entry ID.
        """
        if self.only_one_entry(entry_field=self._entry_field):
            logging.warning('Cannot split the entry IDs of a URL with only one entry ID. Returning the same URL...')

            yield self
        else:
            for entry_id in self._entry_ids:
                split_url = GetKEGGurl(
                    entry_ids=[entry_id], entry_field=self._entry_field
                )

                yield split_url
