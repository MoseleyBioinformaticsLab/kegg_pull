from pytest import raises, mark

from src.kegg_pull.kegg_url import ListKEGGurl, GetKEGGurl, BASE_URL
from tests.utils import assert_expected_error_message, assert_warning


def test_list_kegg_url_validate():
    with raises(ValueError) as e:
        ListKEGGurl(database_type='invalid-database-type')

    assert_expected_error_message(
        expected_message='Cannot create URL - Invalid database type: "invalid-database-type". Valid values are: ag, '
                         'brite, compound, dgroup, disease, drug, enzyme, genome, glycan, ko, module, network, '
                         'organism, pathway, rclass, reaction, variant, vg, vp', e=e
    )


def test_list_kegg_url_create_url_options():
    list_kegg_url = ListKEGGurl(database_type='vg')
    expected_url = f'{BASE_URL}/list/vg'

    assert str(list_kegg_url) == list_kegg_url.url == expected_url


test_get_kegg_url_validate_data: list = [
    ([], None, 'Cannot create URL - Entry IDs must be specified for the KEGG get operation'),
    (
        ['x'], 'invalid-entry-field', 'Cannot create URL - Invalid KEGG entry field: "invalid-entry-field". Valid '
                                      'values are: aaseq, conf, image, json, kcf, kgml, mol, ntseq'
    ),
    (
        ['x', 'y'], 'json', 'Cannot create URL - The KEGG entry field: "json" only supports requests of one KEGG entry '
                            'at a time but 2 entry IDs are provided'
    )
]


@mark.parametrize('entry_ids,entry_field,expected_error_message', test_get_kegg_url_validate_data)
def test_get_kegg_url_validate(entry_ids: list, entry_field: str, expected_error_message: str):
    with raises(ValueError) as e:
        GetKEGGurl(entry_ids=entry_ids, entry_field=entry_field)

    assert_expected_error_message(expected_message=expected_error_message, e=e)


test_get_kegg_url_create_url_options_data: list = [
    (['x'], None, 'get/x'),
    (['x'], 'image', 'get/x/image'),
    (['x'], 'aaseq', 'get/x/aaseq'),
    (['x', 'y'], None, 'get/x+y'),
    (['x', 'y', 'z'], 'ntseq', 'get/x+y+z/ntseq')
]


@mark.parametrize('entry_ids,entry_field,expected_url', test_get_kegg_url_create_url_options_data)
def test_get_kegg_url_create_url_options(entry_ids: list, entry_field: str, expected_url: str):
    get_kegg_url = GetKEGGurl(entry_ids=entry_ids, entry_field=entry_field)
    expected_url = f'{BASE_URL}/{expected_url}'

    assert get_kegg_url.url == expected_url


def test_split_urls_warning(caplog):
    original_url = GetKEGGurl(entry_ids=['x'], entry_field='conf')

    # Ensure there is only one url returned
    returned_urls = list(original_url.split_entries())
    [returned_url] = returned_urls

    # Ensure the returned url is the same object reference as the original
    assert returned_url == original_url

    assert_warning(
        file_name='kegg_url.py', func_name='split_entries',
        message='Cannot split the entry IDs of a URL with only one entry ID. Returning the same URL...', caplog=caplog
    )


test_split_urls_data: list = [
    (['x', 'y', 'z'], None, ['/get/x', '/get/y', '/get/z']),
    (['x', 'y'], 'kcf', ['/get/x/kcf', '/get/y/kcf'])
]


@mark.parametrize('entry_ids,entry_field,expected_urls', test_split_urls_data)
def test_split_entries(entry_ids: list, entry_field: str, expected_urls: list):
    url_to_split = GetKEGGurl(entry_ids=entry_ids, entry_field=entry_field)

    for split_url, expected_url in zip(url_to_split.split_entries(), expected_urls):
        expected_url = BASE_URL + expected_url

        assert split_url.url == expected_url
