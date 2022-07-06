"""
Classes for creating KEGG API URLs for both the list and get API operations
"""
import logging
from abc import ABC, abstractmethod

BASE_URL: str = 'https://rest.kegg.jp'


class AbstractKEGGurl(ABC):
    def __init__(self, api_operation: str, base_url: str = BASE_URL, **kwargs):
        self._validate(**kwargs)
        url_options: str = self._create_url_options(**kwargs)
        self._url = f'{base_url}/{api_operation}/{url_options}'

    @abstractmethod
    def _validate(self, **kwargs):
        pass  # pragma: no cover

    @abstractmethod
    def _create_url_options(self, **kwargs) -> str:
        pass  # pragma: no cover

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

    @classmethod
    def _validate_url_option(cls, option_name: str, option_value: str):
        """ Raises an exception if a provided URL option is not valid
        :param option_name: The name of the type of option to check
        :param option_value: The value of the URL option provided
        :raises ValueError:
        """
        if option_value not in cls._valid_url_options:
            valid_options = ', '.join(sorted(cls._valid_url_options))
            cls._raise_error(reason=f'Invalid {option_name}: "{option_value}". Valid values are: {valid_options}')


class ListKEGGurl(AbstractKEGGurl):
    _valid_url_options = {
        'pathway', 'brite', 'module', 'ko', 'genome', 'vg', 'vp', 'ag', 'compound', 'glycan', 'reaction', 'rclass',
        'enzyme', 'network', 'variant', 'disease', 'drug', 'dgroup', 'organism'
    }

    def __init__(self, database_type: str):
        super().__init__(api_operation='list', database_type=database_type)

    def _validate(self, database_type: str):
        self._validate_url_option(option_name='database type', option_value=database_type)

    def _create_url_options(self, database_type: str) -> str:
        return database_type


class GetKEGGurl(AbstractKEGGurl):
    _valid_url_options = {
        'aaseq': True, 'ntseq': True, 'mol': True, 'kcf': True, 'image': False, 'conf': False, 'kgml': False,
        'json': False
    }

    def __init__(self, entry_ids: list, entry_field: str = None):
        super().__init__(api_operation='get', entry_ids=entry_ids, entry_field=entry_field)
        self._entry_ids = entry_ids
        self._entry_field = entry_field

    def _validate(self, entry_ids: list, entry_field: str):
        n_entry_ids: int = len(entry_ids)

        if n_entry_ids == 0:
            self._raise_error(reason='Entry IDs must be specified for the KEGG get operation')

        if entry_field is not None:
            self._validate_url_option(option_name='KEGG entry field', option_value=entry_field)

            if self.can_only_pull_one_entry(entry_field=entry_field) and n_entry_ids > 1:
                self._raise_error(
                    reason=f'The KEGG entry field: "{entry_field}" only supports requests of one KEGG entry '
                           f'at a time but {n_entry_ids} entry IDs are provided'
                )

    @staticmethod
    def can_only_pull_one_entry(entry_field: str):
        return entry_field is not None and not GetKEGGurl._valid_url_options[entry_field]

    def _create_url_options(self, entry_ids: list, entry_field: str) -> str:
        entry_ids_url_option = '+'.join(entry_ids)

        if entry_field is not None:
            return f'{entry_ids_url_option}/{entry_field}'
        else:
            return entry_ids_url_option

    def split_entries(self):
        if self.can_only_pull_one_entry(entry_field=self._entry_field):
            logging.warning('Cannot split the entry IDs of a URL with only one entry ID. Returning the same URL...')

            yield self
        else:
            for entry_id in self._entry_ids:
                split_url = GetKEGGurl(
                    entry_ids=[entry_id], entry_field=self._entry_field
                )

                yield split_url
