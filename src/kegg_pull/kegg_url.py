"""
Constructing URLs for the KEGG REST API
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Classes for creating and validating KEGG REST API URLs.
"""
import requests as rq
import logging as log
import abc
import typing as t
from . import _utils as u

BASE_URL = 'https://rest.kegg.jp'


class AbstractKEGGurl(abc.ABC):
    """
    Abstract class which validates and constructs URLs for accessing the KEGG REST API and contains the base data and functionality for all KEGG URL classes.

    :ivar str url: The constructed and validated KEGG URL.
    """
    _URL_LENGTH_LIMIT = 4000
    _valid_kegg_databases = {
        'pathway', 'brite', 'module', 'ko', 'genome', 'vg', 'vp', 'ag', 'compound', 'glycan', 'reaction', 'rclass',
        'enzyme', 'network', 'variant', 'disease', 'drug', 'dgroup', 'genes', 'ligand', 'kegg'}
    _valid_medicus_databases = {
        'disease_ja', 'drug_ja', 'dgroup_ja', 'compound_ja', 'brite_ja', 'atc', 'jtc', 'ndc', 'yj'}
    _organism_set: set[str] | None = None

    def __init__(self, rest_operation: str, base_url: str = BASE_URL, **kwargs) -> None:
        """
        :param rest_operation: The KEGG REST API operation in the URL.
        :param base_url: The base URL for accessing the KEGG web API.
        :param kwargs: The arguments used to construct the REST options after they are validated.
        :raises ValueError: Raised if the given arguments cannot construct a valid KEGG URL.
        """
        self._validate(**kwargs)
        url_options = self._create_rest_options(**kwargs)
        self.url = f'{base_url}/{rest_operation}/{url_options}'
        if len(self.url) > AbstractKEGGurl._URL_LENGTH_LIMIT:
            AbstractKEGGurl._raise_error(
                reason=f'The KEGG URL length of {len(self.url)} exceeds the limit of {AbstractKEGGurl._URL_LENGTH_LIMIT}')

    # noinspection PyMethodParameters
    @u.staticproperty
    def organism_set() -> set[str]:
        """ Obtains the set of valid KEGG organism database names by requesting from the KEGG REST API (caches this result so the request only needs to be done once).

        :return: The set of organism database names.
        :raises RuntimeError: Raised in the unlikely case that the request fails.
        """
        if AbstractKEGGurl._organism_set is None:
            url = f'{BASE_URL}/list/organism'
            error_message = 'The request to the KEGG web API {} while fetching the organism set using the URL: {}'
            try:
                response = rq.get(url=url, timeout=60)
            except rq.exceptions.Timeout:
                raise RuntimeError(error_message.format('timed out', url))
            status_code = response.status_code
            if status_code != 200:
                raise RuntimeError(error_message.format(f'failed with status code {status_code}', url))
            organism_list = response.text.strip().split('\n')
            AbstractKEGGurl._organism_set = set[str]()
            for organism in organism_list:
                [code, name, _, _] = organism.strip().split('\t')
                AbstractKEGGurl._organism_set.add(code)
                AbstractKEGGurl._organism_set.add(name)
        return AbstractKEGGurl._organism_set

    @abc.abstractmethod
    def _validate(self, **kwargs) -> None:
        """ Ensures the arguments passed into the constructor result in a valid KEGG URL.

        :param kwargs: The arguments to validate.
        :raises ValueError: Raised if the given arguments cannot construct a valid KEGG URL.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _create_rest_options(self, **kwargs) -> str:
        """ Creates the string at the end part of a KEGG URL to specify the options for a REST API request.

        :param kwargs: The arguments used to create the options.
        :return: The REST API options.
        """
        pass  # pragma: no cover

    def __repr__(self) -> str:
        return self.url

    @staticmethod
    def _raise_error(reason: str) -> None:
        """ Raises an exception for when a URL is not valid.

        :param reason: The reason why the URL was not valid.
        :raises ValueError: The error that is raised.
        """
        raise ValueError(f'Cannot create URL - {reason}')

    @staticmethod
    def _validate_rest_option(option_name: str, option_value: str, valid_rest_options: t.Iterable[str], add_org: bool = False) -> None:
        """ Raises an exception if a provided REST API option is not valid.

        :param option_name: The name of the type of option to check.
        :param option_value: The value of the REST API option provided.
        :param valid_rest_options: The collection of valid options to choose from.
        :param add_org: Whether to add the "<org>" option to the valid options in the error message.
        :raises ValueError: Raised when the provided option is not valid.
        """
        if option_value not in valid_rest_options:
            if add_org:
                valid_rest_options = set(valid_rest_options)
                valid_rest_options.add('<org>')
            valid_options = ', '.join(sorted(valid_rest_options))
            error_reason = f'Invalid {option_name}: "{option_value}". Valid values are: {valid_options}.'
            if add_org:
                error_reason += ' Where <org> is an organism code or T number.'
            AbstractKEGGurl._raise_error(reason=error_reason)

    @staticmethod
    def _validate_database(database: str, extra_databases: set[str] = set[str](), excluded_databases: set[str] = set[str]()) -> None:
        """ Ensures the database provided is a valid KEGG database.

        :param database: The name of the database to validate.
        :param extra_databases: Additional optional database names to add to the core KEGG databases for the validation.
        :param excluded_databases: Optional database names to exclude from the validation. If extra_databases overlaps
        excluded_databases, extra_databases has priority.
        :raises ValueError: Raised when the provided database is not valid.
        """
        if database not in AbstractKEGGurl.organism_set:
            valid_databases = AbstractKEGGurl._valid_kegg_databases.union(AbstractKEGGurl._valid_medicus_databases)
            valid_databases = valid_databases - excluded_databases
            valid_databases = valid_databases.union(extra_databases)
            AbstractKEGGurl._validate_rest_option(
                option_name='database name', option_value=database, valid_rest_options=valid_databases, add_org=True)


class ListKEGGurl(AbstractKEGGurl):
    """Contains URL construction and validation functionality of the KEGG API list operation."""
    def __init__(self, database: str) -> None:
        """
        :param database: The database option for the KEGG list URL.
        :raises ValueError: Raised if the provided database is not valid.
        """
        super().__init__(rest_operation='list', database=database)

    def _validate(self, database: str) -> None:
        """ Ensures the database option is a KEGG database supported by the list operation.

        :param database: The name of the database to check.
        :raises ValueError: Raised if the provided database is not valid.
        """
        AbstractKEGGurl._validate_database(
            database=database, extra_databases={'organism'}, excluded_databases={'genes', 'ligand', 'kegg'})

    def _create_rest_options(self, database: str) -> str:
        """ Implements the KEGG REST API options creation by returning the provided database name (the only option).

        :param database: The database option to return.
        :return: The database option.
        """
        return database


class InfoKEGGurl(AbstractKEGGurl):
    """Contains URL construction and validation functionality of the KEGG API info operation."""
    def __init__(self, database: str) -> None:
        """
        :param database: The database option for the KEGG info URL.
        :raises ValueError: Raised if the provided database is not valid.
        """
        super(InfoKEGGurl, self).__init__(rest_operation='info', database=database)

    def _validate(self, database: str) -> None:
        """ Ensures the database option is a KEGG database supported by the info operation.

        :param database: The name of the database to check.
        :raises ValueError: Raised if the provided database is not valid.
        """
        AbstractKEGGurl._validate_database(
            database=database, excluded_databases=AbstractKEGGurl._valid_medicus_databases)

    def _create_rest_options(self, database: str) -> str:
        """ Implements the KEGG REST API options creation by returning the provided database name (the only option).

        :param database: The database option to return.
        :return: The database option.
        """
        return database


class GetKEGGurl(AbstractKEGGurl):
    """
    Contains URL construction and validation functionality for the KEGG API get operation.

    :cvar str MAX_ENTRY_IDS_PER_URL: The maximum number of entry IDs allowed in a single get KEGG URL.
    :ivar list entry_ids: The entry IDs of the get KEGG URL.
    """
    _entry_fields = {
        'aaseq': True, 'ntseq': True, 'mol': True, 'kcf': True, 'image': False, 'conf': False, 'kgml': False,
        'json': False}
    MAX_ENTRY_IDS_PER_URL = 10

    def __init__(self, entry_ids: list[str], entry_field: str | None = None) -> None:
        """
        :param entry_ids: Specifies which entry IDs go in the first option of the URL.
        :param entry_field: Specifies which entry field goes in the second option.
        :raises ValueError: Raised if the entry IDs or entry field is not valid.
        """
        super().__init__(rest_operation='get', entry_ids=entry_ids, entry_field=entry_field)
        self.entry_ids = entry_ids
        self._entry_field = entry_field

    @property
    def multiple_entry_ids(self) -> bool:
        """Determines whether the get KEGG URL has more than one entry ID."""
        return len(self.entry_ids) > 1

    def _validate(self, entry_ids: list, entry_field: str | None) -> None:
        """ Ensures valid Entry IDs and a valid entry field are provided.

        :param entry_ids: The entry IDs to validate.
        :param entry_field: The entry field to validate.
        :raises ValueError: Raised if the entry IDs or entry field is not valid.
        """
        n_entry_ids = len(entry_ids)
        if n_entry_ids == 0:
            self._raise_error(reason='Entry IDs must be specified for the KEGG get operation')
        max_entry_ids = GetKEGGurl.MAX_ENTRY_IDS_PER_URL
        if n_entry_ids > max_entry_ids:
            self._raise_error(reason=f'The maximum number of entry IDs is {max_entry_ids} but {n_entry_ids} were provided')
        if entry_field is not None:
            AbstractKEGGurl._validate_rest_option(
                option_name='KEGG entry field', option_value=entry_field, valid_rest_options=GetKEGGurl._entry_fields)
            if self.only_one_entry(entry_field=entry_field) and n_entry_ids > 1:
                self._raise_error(
                    reason=f'The KEGG entry field: "{entry_field}" only supports requests of one KEGG entry '
                           f'at a time but {n_entry_ids} entry IDs are provided')

    @staticmethod
    def only_one_entry(entry_field: str | None) -> bool:
        """ Determines whether a KEGG entry field can only be pulled in one entry at a time for the KEGG get API
        operation.

        :param entry_field: The KEGG entry field to check.
        """
        return entry_field is not None and not GetKEGGurl._entry_fields[entry_field]

    @staticmethod
    def is_binary(entry_field: str | None) -> bool:
        """ Determines if the entry field is a binary response or not.

        :param entry_field: The KEGG entry field to check.
        """
        return entry_field == 'image'

    def _create_rest_options(self, entry_ids: list[str], entry_field: str | None) -> str:
        """ Constructs the REST options for the KEGG API get operation.

        :param entry_ids: The entry IDs for the first REST option.
        :param entry_field: The entry field for the second REST option.
        :return: The constructed options.
        """
        entry_ids_url_option = '+'.join(entry_ids)
        if entry_field is not None:
            return f'{entry_ids_url_option}/{entry_field}'
        else:
            return entry_ids_url_option


class KeywordsFindKEGGurl(AbstractKEGGurl):
    """Contains the URL construction and validation functionality for the KEGG API find operation based on the URL form that searches entries by keywords."""
    def __init__(self, database: str, keywords: list[str]) -> None:
        """
        :param database: The database name option for the first part of the URL.
        :param keywords: The keyword options for the second part of the URL.
        :raises ValueError: Raised if the database name is invalid or keywords are not provided.
        """
        super(KeywordsFindKEGGurl, self).__init__(rest_operation='find', database=database, keywords=keywords)

    def _validate(self, database: str, keywords: list[str]) -> None:
        """ Ensures keywords are provided and the database name is valid.

        :param database: The database name to check.
        :param keywords: The keywords to check.
        :raises ValueError: Raised if the database name is invalid or keywords are not provided.
        """
        if len(keywords) == 0:
            self._raise_error(reason='No search keywords specified')
        AbstractKEGGurl._validate_database(database=database, excluded_databases={'brite', 'kegg'})

    def _create_rest_options(self, keywords: list[str], database: str) -> str:
        """ Constructs the options for the URL using the database name followed by the keywords.

        :param keywords: The keywords to go in the options.
        :param database: The database name to go in the options.
        :return: The constructed options.
        """
        keywords_string = '+'.join(keywords)
        return f'{database}/{keywords_string}'


class MolecularFindKEGGurl(AbstractKEGGurl):
    """Contains the URL construction and validation functionality for the KEGG API find operation based on the URL form that uses chemical / molecular attributes of compounds."""
    _valid_molecular_databases = {'compound', 'drug'}

    def __init__(
            self, database: str, formula: str | None = None, exact_mass: float | tuple[float, float] | None = None,
            molecular_weight: int | tuple[int, int] | None = None) -> None:
        """
        :param database: The database name option for the first part of the URL.
        :param formula: The chemical formula option that can go in the second part of the URL.
        :param exact_mass: The exact molecule mass option that can go in the second part of the URL.
        :param molecular_weight: The molecular weight option that can go in the second part of the URL.
        :raises ValueError: Raised if the provided database name or molecular attribute is invalid.
        """
        super(MolecularFindKEGGurl, self).__init__(
            rest_operation='find', database=database, formula=formula, exact_mass=exact_mass, molecular_weight=molecular_weight)

    def _validate(
            self, database: str, formula: str | None = None, exact_mass: float | tuple[float, float] | None = None,
            molecular_weight: int | tuple[int, int] | None = None) -> None:
        """ Ensures a valid database name and molecular attributes are provided.

        :param database: The database name to check.
        :param formula: The chemical formula attribute to check.
        :param exact_mass: The exact mass attribute to check.
        :param molecular_weight: The molecular weight attribute to check.
        :raises ValueError: Raised if the provided database name or molecular attribute is invalid.
        """
        AbstractKEGGurl._validate_rest_option(
            option_name='molecular database name', option_value=database,
            valid_rest_options=MolecularFindKEGGurl._valid_molecular_databases)
        if formula is None and exact_mass is None and molecular_weight is None:
            AbstractKEGGurl._raise_error(reason='Must provide either a chemical formula, exact mass, or molecular weight option')
        if formula is not None and (exact_mass is not None or molecular_weight is not None):
            log.warning(
                'Only a chemical formula, exact mass, or molecular weight is used to construct the URL. Using formula...')
        elif formula is None and exact_mass is not None and molecular_weight is not None:
            log.warning('Both an exact mass and molecular weight are provided. Using exact mass...')
        MolecularFindKEGGurl._validate_range(range_values=exact_mass, range_name='Exact mass')
        MolecularFindKEGGurl._validate_range(range_values=molecular_weight, range_name='Molecular weight')

    @staticmethod
    def _validate_range(range_values: int | float | tuple[int, int] | tuple[float, float] | None, range_name: str) -> None:
        """ Ensures a given range is valid.

        :param range_values: The two end points of the range (start and end).
        :param range_name: The name of the range for the resulting error message in case of an invalid range.
        :raises ValueError: Raised if the range values are not valid.
        """
        if range_values is not None and type(range_values) is tuple:
            if len(range_values) != 2:
                provided_values = ', '.join(str(range_value) for range_value in range_values)
                AbstractKEGGurl._raise_error(
                    f'{range_name} range can only be constructed from 2 values but {len(range_values)} are provided: '
                    f'{provided_values}')
            min_val, max_val = range_values
            if not min_val < max_val:
                AbstractKEGGurl._raise_error(
                    reason=f'The first value in the range must be less than the second. Values provided:'
                           f' {min_val}-{max_val}')

    def _create_rest_options(
            self, database: str, formula: str | None = None, exact_mass: float | tuple[float, float] | None = None,
            molecular_weight: int | tuple[int, int] | None = None) -> str:
        """ Constructs the options for the URL using the database name followed by a molecular attribute.

        :param database: The database name option in the first part of the URL.
        :param formula: The chemical formula option that can go in the second part of the URL.
        :param exact_mass: The exact mass attribute that can go in the second part of the URL.
        :param molecular_weight: The molecular weight attribute that can go in the second part of the URL.
        :return: The constructed options.
        """
        if formula is not None:
            options = f'{formula}/formula'
        elif exact_mass is not None:
            options = MolecularFindKEGGurl._get_range_options(option_name='exact_mass', option_value=exact_mass)
        else:
            options = MolecularFindKEGGurl._get_range_options(option_name='mol_weight', option_value=molecular_weight)
        return f'{database}/{options}'

    @staticmethod
    def _get_range_options(option_name: str, option_value: float | int | tuple[int, int] | tuple[float, float]) -> str:
        """ Constructs options for the URL that are either a single number or a range (start and end separated by a
        dash).

        :param option_name: The name of the option to go in the third part of the URL.
        :param option_value: The single number or range.
        :return: The constructed option.
        """
        if type(option_value) is int or type(option_value) is float:
            options = option_value
        else:
            minimum, maximum = option_value
            options = f'{minimum}-{maximum}'
        return f'{options}/{option_name}'


class AbstractConvKEGGurl(AbstractKEGGurl):
    """Abstract class containing data shared by the KEGG URL classes that validate and construct URLs for the conv KEGG
    REST API operation."""
    _valid_outside_gene_databases = {'ncbi-geneid', 'ncbi-proteinid', 'uniprot'}
    _valid_kegg_molecule_databases = {'compound', 'glycan', 'drug'}
    _valid_outside_molecule_databases = {'pubchem', 'chebi'}

    def __init__(self, **kwargs) -> None:
        """
        :param kwargs: Arguments for the URL validation and construction.
        :raises ValueError: Raised if the provided arguments cannot construct a valid conv KEGG URL.
        """
        super(AbstractConvKEGGurl, self).__init__(rest_operation='conv', **kwargs)

    @abc.abstractmethod
    def _validate(self, **kwargs) -> None:
        """ Validates options for a conv KEGG URL.

        :param kwargs: The options to validate.
        :raises ValueError: Raised if the provided arguments cannot construct a valid conv KEGG URL.
        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def _create_rest_options(self, **kwargs) -> str:
        """ Constructs the options in a conv KEGG URL.

        :param kwargs: The arguments to create the options.
        :return: The constructed options.
        """
        pass  # pragma: no cover


class DatabaseConvKEGGurl(AbstractConvKEGGurl):
    """Contains the URL construction and validation functionality of the KEGG API conv operation based on the URL form that uses a KEGG database and an outside database."""
    def __init__(self, kegg_database: str, outside_database: str) -> None:
        """
        :param kegg_database: The name of the KEGG database.
        :param outside_database: The name of the outside database.
        :raises ValueError: Raised if the database names are not valid or are not of the same type.
        """
        super(DatabaseConvKEGGurl, self).__init__(kegg_database=kegg_database, outside_database=outside_database)

    def _validate(self, kegg_database: str, outside_database: str) -> None:
        """ Ensures that the database names are valid and that they're both the same type

        :param kegg_database: The name of the KEGG database to check.
        :param outside_database: The name of the outside database to check.
        :raises ValueError: Raised if the database names are not valid or are not of the same type.
        """
        # noinspection PyTypeChecker
        valid_kegg_gene_databases: set[str] = AbstractKEGGurl.organism_set
        valid_kegg_molecule_databases = AbstractConvKEGGurl._valid_kegg_molecule_databases
        valid_kegg_databases = valid_kegg_molecule_databases.union(valid_kegg_gene_databases)
        if kegg_database not in valid_kegg_databases:
            AbstractKEGGurl._validate_rest_option(
                option_name='KEGG database', option_value=kegg_database, valid_rest_options=valid_kegg_molecule_databases, add_org=True)
        valid_outside_gene_databases = AbstractConvKEGGurl._valid_outside_gene_databases
        valid_outside_molecule_databases = AbstractConvKEGGurl._valid_outside_molecule_databases
        valid_outside_databases = valid_outside_molecule_databases.union(valid_outside_gene_databases)
        AbstractKEGGurl._validate_rest_option(
            option_name='outside database', option_value=outside_database, valid_rest_options=valid_outside_databases)
        if kegg_database in valid_kegg_gene_databases and outside_database not in valid_outside_gene_databases:
            AbstractKEGGurl._raise_error(
                reason=f'KEGG database "{kegg_database}" is a gene database but outside database '
                       f'"{outside_database}" is not.')
        if kegg_database in valid_kegg_molecule_databases and outside_database not in valid_outside_molecule_databases:
            AbstractKEGGurl._raise_error(
                reason=f'KEGG database "{kegg_database}" is a molecule database but outside database '
                       f'"{outside_database}" is not.')

    def _create_rest_options(self, kegg_database: str, outside_database: str) -> str:
        """ Constructs the REST options by appending the outside database name to the kegg database name

        :param kegg_database: The KEGG database option.
        :param outside_database: The outside database option
        :return: The constructed options.
        """
        return f'{kegg_database}/{outside_database}'


class EntriesConvKEGGurl(AbstractConvKEGGurl):
    """Contains the URL construction and validation functionality for the KEGG API conv operation based on the URL form that uses a target database and entry IDs."""
    def __init__(self, target_database: str, entry_ids: list[str]) -> None:
        """
        :param target_database: The target database option.
        :param entry_ids: The entry IDs options.
        :raises ValueError: Raised if the target database is invalid or entry IDs are not provided.
        """
        super(EntriesConvKEGGurl, self).__init__(target_database=target_database, entry_ids=entry_ids)

    def _validate(self, target_database: str, entry_ids: list[str]) -> None:
        """ Ensures the target database is valid and that the entry IDs are provided.

        :param target_database: The name of the target database to check.
        :param entry_ids: The entry IDs to check.
        :raises ValueError: Raised if the target database is invalid or entry IDs are not provided.
        """
        valid_databases = AbstractConvKEGGurl._valid_kegg_molecule_databases
        valid_databases = valid_databases.union(AbstractConvKEGGurl._valid_outside_gene_databases)
        valid_databases = valid_databases.union(AbstractConvKEGGurl._valid_outside_molecule_databases)
        valid_databases.add('genes')
        # noinspection PyTypeChecker
        if target_database not in valid_databases.union(AbstractKEGGurl.organism_set):
            AbstractKEGGurl._validate_rest_option(
                option_name='target database', option_value=target_database, valid_rest_options=valid_databases, add_org=True)
        if len(entry_ids) == 0:
            self._raise_error(reason='Entry IDs must be specified for this KEGG "conv" operation')

    def _create_rest_options(self, target_database: str, entry_ids: list) -> str:
        """ Constructs the REST options by appending the entry IDs (separated by '+') to the target database name.

        :param target_database: The name of the target database in the first part of the URL.
        :param entry_ids: The entry IDs in the second part of the URL.
        :return: The constructed options.
        """
        return f'{target_database}/{"+".join(entry_ids)}'


class AbstractLinkKEGGurl(AbstractKEGGurl):
    """Abstract class containing the shared data for the link KEGG URLs."""
    _extra_databases = {'atc', 'jtc', 'ndc', 'yj', 'pubmed'}

    def __init__(self, **kwargs) -> None:
        """
        :param kwargs: The arguments to validate and construct the URL.
        :raises ValueError: Raised if the provided arguments are invalid.
        """
        super(AbstractLinkKEGGurl, self).__init__(rest_operation='link', **kwargs)

    @abc.abstractmethod
    def _validate(self, **kwargs) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def _create_rest_options(self, **kwargs) -> str:
        pass  # pragma: no cover


class DatabaseLinkKEGGurl(AbstractLinkKEGGurl):
    """Contains the URL construction and validation functionality for the link KEGG REST API operation of the form that uses a target database and a source database."""

    def __init__(self, target_database: str, source_database: str) -> None:
        """
        :param target_database: The name of the target database option.
        :param source_database: The name of the source database option.
        :raises ValueError: Raised if the databases are invalid.
        """
        super(DatabaseLinkKEGGurl, self).__init__(target_database=target_database, source_database=source_database)

    def _validate(self, target_database: str, source_database: str) -> None:
        """ Ensures the provided databases are valid

        :param target_database: The name of the target database to check.
        :param source_database: The name of the source database to check.
        :raises ValueError: Raised if the databases are invalid.
        """
        if target_database == source_database:
            AbstractKEGGurl._raise_error(
                reason=f'The source and target database cannot be identical. Database selected: {source_database}.')
        excluded_databases = AbstractKEGGurl._valid_medicus_databases.union({'kegg', 'genes', 'ligand'})
        AbstractKEGGurl._validate_database(
            database=target_database, extra_databases=AbstractLinkKEGGurl._extra_databases, excluded_databases=excluded_databases)
        AbstractKEGGurl._validate_database(
            database=source_database, extra_databases=AbstractLinkKEGGurl._extra_databases, excluded_databases=excluded_databases)

    def _create_rest_options(self, target_database: str, source_database: str) -> str:
        """ Constructs the options by appending the target database name to the source database name

        :param target_database: The target database name for the first option.
        :param source_database: The source database name for the second option.
        :return: The constructed options.
        """
        return f'{target_database}/{source_database}'


class EntriesLinkKEGGurl(AbstractLinkKEGGurl):
    """Contains the URL construction and validation functionality for the link KEGG REST API operation of the form that uses a target database and entry IDs."""
    def __init__(self, target_database: str, entry_ids: list[str]) -> None:
        """
        :param target_database: The name of the target database option.
        :param entry_ids: The entry IDs options.
        :raises ValueError: Raised if the target database is invalid or entry IDs are not provided.
        """
        super(EntriesLinkKEGGurl, self).__init__(target_database=target_database, entry_ids=entry_ids)

    def _validate(self, target_database: str, entry_ids: list[str]) -> None:
        """ Ensures the target database name is valid and that the entry IDs are provided.

        :param target_database: The name of the target database to check.
        :param entry_ids: The entry IDs to check.
        :raises ValueError: Raised if the target database is invalid or entry IDs are not provided.
        """
        excluded_databases: set = AbstractKEGGurl._valid_medicus_databases.union({'kegg', 'ligand'})
        AbstractKEGGurl._validate_database(
            database=target_database, extra_databases=AbstractLinkKEGGurl._extra_databases, excluded_databases=excluded_databases)
        if len(entry_ids) == 0:
            AbstractKEGGurl._raise_error(reason='At least one entry ID must be specified to perform the link operation')

    def _create_rest_options(self, target_database: str, entry_ids: list[str]) -> str:
        """Constructs the options by appending the entry IDs (separated by '+') to the target database name.

        :param target_database: The name of the target database for the first options.
        :param entry_ids: The entry IDs as the last options.
        :return: The constructed options.
        """
        return f'{target_database}/{"+".join(entry_ids)}'


class DdiKEGGurl(AbstractKEGGurl):
    """Contains the URL construction and validation functionality for the ddi KEGG REST operation."""
    def __init__(self, drug_entry_ids: list[str]) -> None:
        """
        :param drug_entry_ids: The entry IDs for a drug database.
        :raises ValueError: Raised if the drug entry IDs are not provided.
        """
        super(DdiKEGGurl, self).__init__(rest_operation='ddi', drug_entry_ids=drug_entry_ids)

    def _validate(self, drug_entry_ids: list) -> None:
        """ Ensures the drug entry IDs are provided.

        :param drug_entry_ids: The drug entry IDs to check.
        :raises ValueError: Raised if the drug entry IDs are not provided.
        """
        if len(drug_entry_ids) == 0:
            AbstractKEGGurl._raise_error(reason='At least one drug entry ID must be specified for the DDI operation')

    def _create_rest_options(self, drug_entry_ids: list) -> str:
        """ Constructs the options by separating the drug entry IDs by '+'.

        :param drug_entry_ids: The drug entry ID options.
        :return: The constructed options.
        """
        return "+".join(drug_entry_ids)
