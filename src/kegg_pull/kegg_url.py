"""
Classes for creating KEGG REST API URLs for both the list and get API operations.
"""
import requests as rq
import logging as l
import abc
import typing as t

BASE_URL: str = 'https://rest.kegg.jp'


class AbstractKEGGurl(abc.ABC):
    """
    Abstract class containing the base data and functionality for all KEGG URL classes which validate and construct URLs
    for accessing the KEGG web API.
    """
    __valid_kegg_databases = {
        'pathway', 'brite', 'module', 'ko', 'genome', 'vg', 'vp', 'ag', 'compound', 'glycan', 'reaction', 'rclass',
        'enzyme', 'network', 'variant', 'disease', 'drug', 'dgroup'
    }

    __organism_set = None

    def __init__(self, rest_operation: str, base_url: str = BASE_URL, **kwargs):
        """ Validates the arguments and constructs the KEGG API URL from them.

        :param rest_operation: The KEGG API operation in the URL
        :param base_url: The base URL for accessing the KEGG web API
        :param kwargs: The arguments used to construct the URL options after they are validated
        """
        self._validate(**kwargs)
        url_options: str = self._create_rest_options(**kwargs)
        self._url = f'{base_url}/{rest_operation}/{url_options}'

    @staticmethod
    def __get_organism_set() -> set:
        if AbstractKEGGurl.__organism_set is None:
            url = f'{BASE_URL}/list/organism'
            error_message = 'The request to the KEGG web API {} while fetching the organism list using the URL: {}'

            try:
                response: rq.Response = rq.get(url=url, timeout=60)
            except rq.exceptions.Timeout:
                raise RuntimeError(
                    error_message.format('timed out', url)
                )

            if response.status_code != 200:
                raise RuntimeError(
                    error_message.format('failed', url)
                )

            organism_list: list = response.text.strip().split('\n')
            AbstractKEGGurl.__organism_set = set()

            for organism in organism_list:
                [code, name, _, _] = organism.strip().split('\t')
                AbstractKEGGurl.__organism_set.add(code)
                AbstractKEGGurl.__organism_set.add(name)

        return AbstractKEGGurl.__organism_set

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

    @staticmethod
    def _validate_rest_option(option_name: str, option_value: str, valid_rest_options: t.Iterable):
        """ Raises an exception if a provided REST API option is not valid.

        :param option_name: The name of the type of option to check
        :param option_value: The value of the REST API option provided
        :param valid_rest_options: The collection of valid options to choose from
        :raises ValueError:
        """
        if option_value not in valid_rest_options:
            valid_options = ', '.join(sorted(valid_rest_options))

            AbstractKEGGurl._raise_error(
                reason=f'Invalid {option_name}: "{option_value}". Valid values are: {valid_options}'
            )

    @staticmethod
    def _validate_database_name(database_name):
        """ Ensures the database provided is a valid KEGG database.

        :param database_name: The name of the database to validate
        """
        if database_name not in AbstractKEGGurl.__get_organism_set():
            AbstractKEGGurl._validate_rest_option(
                option_name='database name', option_value=database_name,
                valid_rest_options=AbstractKEGGurl.__valid_kegg_databases
            )


class DatabaseOnlyKEGGurl(AbstractKEGGurl):
    """Contains the validation implementation and URL construction of KEGG URL classes with only a database option"""
    def _validate(self, database_name: str):
        """ Ensures the database option is a valid KEGG database.

        :param database_name: The name of the database to check.
        """
        self._validate_database_name(database_name=database_name)

    def _create_rest_options(self, database_name: str) -> str:
        """ Implements the KEGG REST API options creation by returning the provided database name (the only option).

        :param database_name: The database option to return.
        """
        return database_name


class ListKEGGurl(DatabaseOnlyKEGGurl):
    """Contains the validation implementation and URL construction of the KEGG API list operation."""
    def __init__(self, database_name: str):
        """ Validates and constructs a KEGG URL for the list API operation.

        :param database_name: The database option for the KEGG list URL
        """
        super().__init__(rest_operation='list', database_name=database_name)

    def _validate(self, database_name: str):
        """ Ensures the database name is a valid KEGG database if "organism" is not provided

        :param database_name: Either a KEGG database or "organism"
        """
        if database_name != 'organism':
            super(ListKEGGurl, self)._validate(database_name=database_name)


class InfoKEGGurl(DatabaseOnlyKEGGurl):
    """Contains the validation implementation and URL construction of the KEGG API info operation"""
    def __init__(self, database_name: str):
        """ Validates and constructs a KEGG URL for the info API operation.

        :param database_name: The database option for the KEGG info URL.
        """
        super(InfoKEGGurl, self).__init__(kegg_rest_operation='info', database_name=database_name)


class GetKEGGurl(AbstractKEGGurl):
    """Contains validation and URL construction as well as a helpful interface for the KEGG API get operation."""
    _entry_fields = {
        'aaseq': True, 'ntseq': True, 'mol': True, 'kcf': True, 'image': False, 'conf': False, 'kgml': False,
        'json': False
    }

    MAX_ENTRY_IDS_PER_URL = 10

    def __init__(self, entry_ids: list, entry_field: str = None):
        """ Validates and constructs the entry IDs and entry field options.

        :param entry_ids: Specifies which entry IDs go in the first option of the URL
        :param entry_field: Specifies which entry field goes in the second option
        """
        super().__init__(rest_operation='get', entry_ids=entry_ids, entry_field=entry_field)
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

        max_entry_ids: int = GetKEGGurl.MAX_ENTRY_IDS_PER_URL

        if n_entry_ids > max_entry_ids:
            self._raise_error(
                reason=f'The maximum number of entry IDs is {max_entry_ids} but {n_entry_ids} were provided'
            )

        if entry_field is not None:
            AbstractKEGGurl._validate_rest_option(
                option_name='KEGG entry field', option_value=entry_field, valid_rest_options=GetKEGGurl._entry_fields
            )

            if self.only_one_entry(entry_field=entry_field) and n_entry_ids > 1:
                self._raise_error(
                    reason=f'The KEGG entry field: "{entry_field}" only supports requests of one KEGG entry '
                           f'at a time but {n_entry_ids} entry IDs are provided'
                )

    @staticmethod
    def only_one_entry(entry_field: str) -> bool:
        """ Determines whether a KEGG entry field can only be pulled in one entry at a time for the KEGG get API
        operation.

        :param entry_field: The KEGG entry field to check
        """
        return entry_field is not None and not GetKEGGurl._entry_fields[entry_field]

    @staticmethod
    def is_binary(entry_field: str) -> bool:
        """ Determines if the entry field is a binary response or not.

        :param entry_field: The KEGG entry field to check
        """
        return entry_field == 'image'

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


class KeywordsFindKEGGurl(AbstractKEGGurl):
    def __init__(self, database_name: str, keywords: list):
        super(KeywordsFindKEGGurl, self).__init__(rest_operation='find', database_name=database_name, keywords=keywords)

    def _validate(self, database_name: str, keywords: list):
        if database_name == 'brite':
            self._raise_error(reason='Key words search not supported for brite entries')

        if len(keywords) == 0:
            self._raise_error(reason='No search keywords specified')

        AbstractKEGGurl._validate_database_name(database_name=database_name)

    def _create_rest_options(self, keywords: list, database_name: str) -> str:
        keywords_string = '+'.join(keywords)

        return f'{database_name}/{keywords_string}'


class MolecularFindKEGGurl(AbstractKEGGurl):
    _valid_molecular_databases = {'compound', 'drug'}

    def __init__(self, database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
        molecular_weight: t.Union[int, tuple] = None
    ):
        super(MolecularFindKEGGurl, self).__init__(
            rest_operation='find', database_name=database_name, formula=formula, exact_mass=exact_mass,
            molecular_weight=molecular_weight
        )

    def _validate(
        self, database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
        molecular_weight: t.Union[int, tuple] = None
    ):
        AbstractKEGGurl._validate_rest_option(
            option_name='molecular database name', option_value=database_name,
            valid_rest_options=MolecularFindKEGGurl._valid_molecular_databases
        )

        if formula is None and exact_mass is None and molecular_weight is None:
            AbstractKEGGurl._raise_error(
                reason='Must provide either a chemical formula, exact mass, or molecular weight option'
            )

        if formula is not None and (exact_mass is not None or molecular_weight is not None):
            l.warning(
                'Only a chemical formula, exact mass, or molecular weight is used to construct the URL. Using formula'
                '...'
            )

        if formula is None and exact_mass is not None and molecular_weight is not None:
            l.warning('Both an exact mass and molecular weight are provided. Using exact mass...')

        MolecularFindKEGGurl._validate_range(range_values=exact_mass, range_name='Exact mass')
        MolecularFindKEGGurl._validate_range(range_values=molecular_weight, range_name='Molecular weight')

    @staticmethod
    def _validate_range(range_values: tuple, range_name: str):
        if range_values is not None and type(range_values) is tuple:
            if len(range_values) != 2:
                AbstractKEGGurl._raise_error(
                    f'{range_name} range can only be constructed from 2 values but {len(range_values)} are provided: '
                    f'{", ".join(range_values)}'
                )

            min_val, max_val = range_values

            if not min_val < max_val:
                AbstractKEGGurl._raise_error(
                    reason=f'The first value in the range must be less than the second. Values provided:'
                           f' {min_val}-{max_val}'
                )

    def _create_rest_options(self, database_name: str, formula: str = None, exact_mass: t.Union[float, tuple] = None,
        molecular_weight: t.Union[int, tuple] = None
    ) -> str:
        if formula is not None:
            options = f'{formula}/formula'
        elif exact_mass is not None:
            options = MolecularFindKEGGurl._get_range_options(option_name='exact_mass', option_value=exact_mass)
        else:
            options = MolecularFindKEGGurl._get_range_options(option_name='mol_weight', option_value=molecular_weight)

        return f'{database_name}/{options}'

    @staticmethod
    def _get_range_options(option_name: str, option_value: t.Union[float, int, tuple]) -> str:
        if type(option_value) is int or type(option_value) is float:
            options = option_value
        else:
            minimum, maximum = option_value

            options = f'{minimum}-{maximum}'

        return f'{options}/{option_name}'
