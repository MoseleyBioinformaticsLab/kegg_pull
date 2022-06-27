BASE_URL: str = 'https://rest.kegg.jp'


class GenericKEGGurl:
    _valid_url_values: dict = {
        'list': {
            'pathway', 'brite', 'module', 'ko', 'genome', 'vg', 'vp', 'ag', 'compound', 'glycan', 'reaction', 'rclass',
            'enzyme', 'network', 'variant', 'disease', 'drug', 'dgroup', 'organism'
        },
        'get': {
            'aaseq': True, 'ntseq': True, 'mol': True, 'kcf': True, 'image': False, 'conf': False, 'kgml': False,
            'json': False
        }
    }

    def __init__(
        self, kegg_api_operation: str, pull_format: str = None, database_type: str = None, entry_ids: list = None,
        base_url=BASE_URL
    ):
        self._validate(
            kegg_api_operation=kegg_api_operation, database_type=database_type, pull_format=pull_format,
            entry_ids=entry_ids
        )

        self._entry_ids = entry_ids

        self._url: str = self._creat_url(
            kegg_api_operation=kegg_api_operation, pull_format=pull_format, database_type=database_type,
            entry_ids=entry_ids, base_url=base_url
        )

    def __repr__(self):
        return self.url

    @property
    def url(self):
        return self._url

    @property
    def entry_ids(self):
        return self._entry_ids

    def _validate(self, kegg_api_operation: str, database_type: str, pull_format: str, entry_ids: list):
        if kegg_api_operation == 'list':
            if database_type is None:
                self._raise_error(reason='A database must be specified for the KEGG list operation')

            self._validate_operation_option(
                operation=kegg_api_operation, option_name='database name', option_value=database_type
            )
        elif kegg_api_operation == 'get':
            if entry_ids is None or len(entry_ids) == 0:
                self._raise_error(reason='Entry IDs must be specified for the KEGG get operation')

            if pull_format is not None:
                self._validate_operation_option(
                    operation=kegg_api_operation, option_name='entry field type', option_value=pull_format
                )

                n_entry_ids: int = len(entry_ids)

                if self._can_only_pull_one_entry(pull_format=pull_format) and n_entry_ids > 1:
                    self._raise_error(
                        reason=f'The entry field type: "{pull_format}" only supports requests of one KEGG object at a'
                               f' time but {n_entry_ids} entry IDs are provided'
                    )
        else:
            self._raise_invalid_values_error(
                value_name='KEGG API operation', value=kegg_api_operation, valid_values=self._valid_url_values.keys()
            )

    @staticmethod
    def _raise_error(reason: str):
        raise ValueError(f'Cannot create URL - {reason}')

    def _validate_operation_option(self, operation: str, option_name: str, option_value: str):
        valid_values: set = self._valid_url_values[operation]

        if option_value not in valid_values:
            self._raise_invalid_values_error(value_name=option_name, value=option_value, valid_values=valid_values)

    def _raise_invalid_values_error(self, value_name: str, value: str, valid_values: iter):
        valid_values: str = ', '.join(sorted(valid_values))

        self._raise_error(
            reason=f'Invalid {value_name}: "{value}". Valid values are: {valid_values}'
        )

    def _can_only_pull_one_entry(self, pull_format: str):
        return not self._valid_url_values['get'][pull_format]

    @staticmethod
    def _creat_url(
        kegg_api_operation: str, pull_format: str = None, database_type: str = None, entry_ids: list = None,
        base_url=BASE_URL
    ) -> str:
        if kegg_api_operation == 'list':
            return f'{base_url}/list/{database_type}'
        else:
            entry_ids_url_option: str = '+'.join(entry_ids)

            if pull_format is not None:
                return f'{base_url}/get/{entry_ids_url_option}/{pull_format}'
            else:
                return f'{base_url}/get/{entry_ids_url_option}'
