from pytest import raises, mark

from src.kegg_pull.generic_kegg_url import GenericKEGGurl, BASE_URL
from tests.utils import assert_expected_error_message, assert_warning


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


entry_ids_unspecified_message: str = 'Cannot create URL - Entry IDs must be specified for the KEGG get operation'

test_validate_data: list = [
    ({'kegg_api_operation': 'list'}, 'Cannot create URL - A database must be specified for the KEGG list operation'),
    (
        {'kegg_api_operation': 'list', 'pull_format': 'kgml'},
        'Cannot create URL - Entry IDs and entry field types are for the KEGG get operation and are not supported by '
        'the KEGG list operation'
    ),
    (
        {'kegg_api_operation': 'list', 'entry_ids': ['x', 'y']},
        'Cannot create URL - Entry IDs and entry field types are for the KEGG get operation and are not supported by '
        'the KEGG list operation'
    ),
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
    expected_url: str = BASE_URL + expected_url

    assert str(generic_kegg_url) == expected_url
    assert generic_kegg_url.url == expected_url


def test_split_urls_error():
    with raises(ValueError) as e:
        generic_kegg_url: GenericKEGGurl = GenericKEGGurl(kegg_api_operation='list', database_type='enzyme')

        for _ in generic_kegg_url.split_entries():  # pragma: no cover
            pass  # pragma: no cover

    assert_expected_error_message(
        expected_message='Only URLs for a KEGG get operation have entry IDs that can be split', e=e
    )


def test_split_urls_warning(caplog):
    original_url: GenericKEGGurl = GenericKEGGurl(kegg_api_operation='get', entry_ids=['x'], pull_format='conf')

    # Ensure there is only one url returned
    returned_urls: list = list(original_url.split_entries())
    [returned_url] = returned_urls

    # Ensure the returned url is the same object reference as the original
    assert original_url == returned_url

    assert_warning(
        file_name='generic_kegg_url.py', func_name='split_entries',
        message='Cannot split the entry IDs of a URL with only one entry ID. Returning the same URL...', caplog=caplog
    )


test_split_urls_data: list = [
    ({'entry_ids': ['x', 'y', 'z']}, ['/get/x', '/get/y', '/get/z']),
    ({'entry_ids': ['x', 'y'], 'pull_format': 'kcf'}, ['/get/x/kcf', '/get/y/kcf'])
]


@mark.parametrize('kwargs,expected_urls', test_split_urls_data)
def test_split_entries(kwargs: dict, expected_urls: list):
    url_to_split: GenericKEGGurl = GenericKEGGurl('get', **kwargs)

    for split_url, expected_url in zip(url_to_split.split_entries(), expected_urls):
        expected_url: str = BASE_URL + expected_url

        assert split_url.url == expected_url
