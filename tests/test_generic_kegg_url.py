from pytest import raises, mark, ExceptionInfo

from src.kegg_pull.generic_kegg_url import GenericKEGGurl


test_raise_invalid_values_error_data: list = [
    (
        {'kegg_api_operation': 'list', 'database_type': 'invalid-database'}, 'database name', 'invalid-database',
        'ag, brite, compound, dgroup, disease, drug, enzyme, genome, glycan, ko, module, network, organism, pathway,'
        ' rclass, reaction, variant, vg, vp'
    ),
    (
        {'kegg_api_operation': 'get', 'pull_format': 'invalid-pull-format', 'entry_ids': ['']}, 'entry field type',
        'invalid-pull-format', 'aaseq, conf, image, json, kcf, kgml, mol, ntseq'
    ),
    ({'kegg_api_operation': 'invalid-operation'}, 'KEGG API operation', 'invalid-operation', 'get, list'),
]


@mark.parametrize('kwargs,value_name,value,valid_values', test_raise_invalid_values_error_data)
def test_raise_invalid_values_error(kwargs: dict, value_name: str, value: str, valid_values: str):
    with raises(ValueError) as e:
        GenericKEGGurl(**kwargs)

    expected_message: str = f'Cannot create URL - Invalid {value_name}: "{value}". Valid values are: {valid_values}'

    assert_expected_error_message(expected_message=expected_message, e=e)


def assert_expected_error_message(expected_message: str, e: ExceptionInfo):
    actual_message: str = str(e.value)

    assert actual_message == expected_message


entry_ids_unspecified_message: str = 'Cannot create URL - Entry IDs must be specified for the KEGG get operation'

test_validate_data: list = [
    ({'kegg_api_operation': 'list'}, 'Cannot create URL - A database must be specified for the KEGG list operation'),
    ({'kegg_api_operation': 'get'}, entry_ids_unspecified_message),
    ({'kegg_api_operation': 'get', 'entry_ids': []}, entry_ids_unspecified_message),
    (
        {'kegg_api_operation': 'get', 'entry_ids': ['x', 'y'], 'pull_format': 'json'},
        'Cannot create URL - The entry field type: "json" only supports requests of one KEGG object at a time but 2'
        ' entry IDs are provided'
    )
]


@mark.parametrize('kwargs,expected_message', test_validate_data)
def test_validate(kwargs: dict, expected_message: str):
    with raises(ValueError) as e:
        GenericKEGGurl(**kwargs)

    assert_expected_error_message(expected_message=expected_message, e=e)


test_create_url_data: list = [
    ({'kegg_api_operation': 'list', 'database_type': 'module'}, '/list/module'),
    ({'kegg_api_operation': 'get', 'entry_ids': ['x']}, '/get/x'),
    ({'kegg_api_operation': 'get', 'entry_ids': ['x'], 'pull_format': 'image'}, '/get/x/image'),
    ({'kegg_api_operation': 'get', 'entry_ids': ['x'], 'pull_format': 'aaseq'}, '/get/x/aaseq'),
    ({'kegg_api_operation': 'get', 'entry_ids': ['x', 'y']}, '/get/x+y'),
    ({'kegg_api_operation': 'get', 'entry_ids': ['x', 'y', 'z'], 'pull_format': 'ntseq'}, '/get/x+y+z/ntseq'),
    ({'kegg_api_operation': 'get', 'entry_ids': ['x', 'y', 'z'], 'pull_format': 'mol'}, '/get/x+y+z/mol')
]


@mark.parametrize('kwargs,expected_url', test_create_url_data)
def test_create_url(kwargs: dict, expected_url: str):
    generic_kegg_url: GenericKEGGurl = GenericKEGGurl(**kwargs)

    if 'entry_ids' in kwargs:
        actual_entry_ids_url_option: str = generic_kegg_url.url.split('/')[4]
        expected_entry_ids_url_option: str = '+'.join(generic_kegg_url.entry_ids)

        assert actual_entry_ids_url_option == expected_entry_ids_url_option

    base_url: str = 'https://rest.kegg.jp'
    expected_url: str = base_url + expected_url

    assert str(generic_kegg_url) == expected_url
    assert generic_kegg_url.url == expected_url
