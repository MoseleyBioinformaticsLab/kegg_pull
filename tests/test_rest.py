import pytest as pt
import requests as rq
import unittest.mock as mock
import os
import typing as t

import kegg_pull.rest as r
import kegg_pull.kegg_url as ku
import tests.utils as u


test_kegg_response_exception_data = [
    ({'status': None, 'kegg_url': None}, 'A status must be specified for the KEGG response'),
    (
        {'status': r.KEGGresponse.Status.SUCCESS, 'kegg_url': None},
        'A KEGG response cannot be marked as successful if its response body is empty'
    )
]
@pt.mark.parametrize('kwargs,expected_message', test_kegg_response_exception_data)
def test_kegg_response_exception(kwargs: dict, expected_message: str):
    with pt.raises(ValueError) as error:
        r.KEGGresponse(**kwargs)

    u.assert_expected_error_message(expected_message=expected_message, error=error)


def test_kegg_rest_exception():
    with pt.raises(ValueError) as error:
        r.KEGGrest(n_tries=0)

    expected_message = '0 is not a valid number of tries to make a KEGG request.'
    u.assert_expected_error_message(expected_message=expected_message, error=error)


def test_request_and_test_success(mocker):
    kegg_rest = r.KEGGrest()
    text_mock = 'text mock'
    content_mock = b'content mock'
    response_mock = mocker.MagicMock(text=text_mock, content=content_mock, status_code=200)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.get', return_value=response_mock)
    url_mock = 'url mock'
    kegg_url_mock = mocker.MagicMock(url=url_mock)
    create_url_spy = mocker.spy(r.KEGGrest, '_get_kegg_url')
    kegg_response: r.KEGGresponse = kegg_rest.request(kegg_url=kegg_url_mock)
    create_url_spy.assert_called_once_with(KEGGurl=None, kegg_url=kegg_url_mock)
    get_mock.assert_called_once_with(url=url_mock, timeout=60)

    assert kegg_response.status == r.KEGGresponse.Status.SUCCESS
    assert kegg_response.text_body == text_mock
    assert kegg_response.binary_body == content_mock
    assert kegg_response.kegg_url == kegg_url_mock

    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.head', return_value=response_mock)
    success: bool = kegg_rest.test(kegg_url=kegg_url_mock)
    head_mock.assert_called_once_with(url=url_mock, timeout=60)

    assert success == True


def test_request_and_test_failed(mocker):
    n_tries = 4
    kegg_rest = r.KEGGrest(n_tries=4)
    url_mock = 'url mock'
    kegg_url_mock = mocker.MagicMock(url=url_mock)
    failed_status_code = 400
    response_mock = mocker.MagicMock(text='', content=b'', status_code=failed_status_code)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.get', return_value=response_mock)
    kegg_response: r.KEGGresponse = kegg_rest.request(kegg_url=kegg_url_mock)
    get_mock.assert_has_calls(mocker.call(url=url_mock, timeout=60) for _ in range(n_tries))

    assert kegg_response.status == r.KEGGresponse.Status.FAILED
    assert kegg_response.kegg_url == kegg_url_mock
    assert kegg_response.text_body is None
    assert kegg_response.binary_body is None

    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.head', return_value=response_mock)
    success: bool = kegg_rest.test(kegg_url=kegg_url_mock)
    head_mock.assert_has_calls(mocker.call(url=url_mock, timeout=60) for _ in range(n_tries))

    assert success == False


def test_request_and_test_timeout(mocker):
    n_tries = 2
    time_out = 30
    sleep_time = 10.5
    kegg_rest = r.KEGGrest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    url_mock = 'url mock'
    kegg_url_mock = mocker.MagicMock(url=url_mock)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.get', side_effect=rq.exceptions.Timeout())
    sleep_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.t.sleep')
    kegg_response: r.KEGGresponse = kegg_rest.request(kegg_url=kegg_url_mock)
    get_mock.assert_has_calls(mocker.call(url=url_mock, timeout=time_out) for _ in range(n_tries))
    sleep_mock.assert_has_calls(mocker.call(sleep_time) for _ in range(n_tries))

    assert kegg_response.status == r.KEGGresponse.Status.TIMEOUT
    assert kegg_response.kegg_url == kegg_url_mock
    assert kegg_response.text_body is None
    assert kegg_response.binary_body is None

    sleep_mock.reset_mock()
    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.head', side_effect=rq.exceptions.Timeout())
    success: bool = kegg_rest.test(kegg_url=kegg_url_mock)
    head_mock.assert_has_calls(mocker.call(url=url_mock, timeout=time_out) for _ in range(n_tries))
    sleep_mock.assert_has_calls(mocker.call(sleep_time) for _ in range(n_tries))

    assert success == False


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=r, subcommand='rest')


test_main_exception_data = [
    ('The request to the KEGG web API failed with the following URL: url/mock', r.KEGGresponse.Status.FAILED),
    ('The request to the KEGG web API timed out with the following URL: url/mock', r.KEGGresponse.Status.TIMEOUT)
]
@pt.mark.parametrize('expected_message,status', test_main_exception_data)
def test_main_exception(mocker, expected_message: str, status):
    mocker.patch(
        'kegg_pull.rest.KEGGrest.info',
        return_value=mocker.MagicMock(status=status, kegg_url=mocker.MagicMock(url='url/mock'))
    )

    mocker.patch('sys.argv', ['kegg_pull', 'rest', 'info', 'db-name'])

    with pt.raises(RuntimeError) as error:
        r.main()

    u.assert_expected_error_message(expected_message=expected_message, error=error)


test_main_data = [
    ('info', ['info', 'ligand'], {'database_name': 'ligand'}, False),
    ('list', ['list', 'module'], {'database_name': 'module'}, False),
    ('get', ['get', 'x,y,z'], {'entry_ids': ['x', 'y', 'z'], 'entry_field': None}, False),
    ('get', ['get', 'a', '--entry-field=image'], {'entry_ids': ['a'], 'entry_field': 'image'}, True),
    ('keywords_find', ['find', 'pathway', 'a,b,c'], {'database_name': 'pathway', 'keywords': ['a', 'b', 'c']}, False),
    (
        'molecular_find', ['find', 'drug', '--formula=CO2'],
        {'database_name': 'drug', 'formula': 'CO2', 'exact_mass': None, 'molecular_weight': None}, False
    ),
    (
        'molecular_find', ['find', 'drug', '--exact-mass=20.2'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': 20.2, 'molecular_weight': None}, False
    ),
    (
        'molecular_find', ['find', 'drug', '--molecular-weight=202'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': 202}, False
    ),    (
        'molecular_find', ['find', 'drug', '--exact-mass=20.2', '--exact-mass=30.3'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': (20.2,30.3), 'molecular_weight': None}, False
    ),
    (
        'molecular_find', ['find', 'drug', '--molecular-weight=202', '--molecular-weight=303'],
        {'database_name': 'drug', 'formula': None, 'exact_mass': None, 'molecular_weight': (202,303)}, False
    ),
    (
        'database_conv', ['conv', 'kegg-db', 'out-db'],
        {'kegg_database_name': 'kegg-db', 'outside_database_name': 'out-db'}, False
    ),
    (
        'entries_conv', ['conv', '--conv-target=genes', 'eid1,eid2'],
        {'target_database_name': 'genes', 'entry_ids': ['eid1', 'eid2']}, False
    ),
    (
        'database_link', ['link', 'target-db', 'source-db'],
        {'target_database_name': 'target-db', 'source_database_name': 'source-db'}, False
    ),
    (
        'entries_link', ['link', '--link-target=target-db', 'x,y'],
        {'target_database_name': 'target-db', 'entry_ids': ['x', 'y']}, False
    ),
    ('ddi', ['ddi', 'de1,de2,de3'], {'drug_entry_ids': ['de1', 'de2', 'de3']}, False)
]
@pt.mark.parametrize('rest_method,args,kwargs,is_binary', test_main_data)
def test_main_print(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, caplog):
    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    kegg_response_mock: mocker.MagicMock = _test_main(mocker=mocker, rest_method=rest_method, args=args, kwargs=kwargs)

    if is_binary:
        u.assert_warning(message='Printing binary response body', caplog=caplog)
        print_mock.assert_called_once_with(kegg_response_mock.binary_body)
    else:
        print_mock.assert_called_once_with(kegg_response_mock.text_body)


def _test_main(mocker, rest_method: str, args: list, kwargs: dict) -> mock.MagicMock:
    argv_mock = ['kegg_pull', 'rest']
    argv_mock.extend(args)
    mocker.patch('sys.argv', argv_mock)

    kegg_response_mock = mocker.MagicMock(
        status=r.KEGGresponse.Status.SUCCESS, text_body='text body mock', binary_body=b'binary body mock'
    )

    rest_method_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.rest.KEGGrest.{rest_method}', return_value=kegg_response_mock
    )

    r.main()
    rest_method_mock.assert_called_once_with(**kwargs)

    return kegg_response_mock


@pt.fixture(name='output_file')
def output_file_mock():
    output_file = 'output.txt'

    yield output_file

    os.remove(output_file)


@pt.mark.parametrize('rest_method,args,kwargs,is_binary', test_main_data)
def test_main_file(mocker, rest_method: str, args: list, kwargs: dict, is_binary: bool, output_file: str):
    args.append(f'--output={output_file}')
    kegg_response: mocker.MagicMock = _test_main(mocker=mocker, rest_method=rest_method, args=args, kwargs=kwargs)

    if is_binary:
        read_type = 'rb'
        expected_file_contents: bytes = kegg_response.binary_body
    else:
        read_type = 'r'
        expected_file_contents: str = kegg_response.text_body

    with open(output_file, read_type) as file:
        actual_file_contents: t.Union[str, bytes] = file.read()

        assert actual_file_contents == expected_file_contents


test_rest_data = [
    (ku.ListKEGGurl, r.KEGGrest.list, {'database_name': 'module'}),
    (ku.GetKEGGurl, r.KEGGrest.get, {'entry_ids': ['xyz'], 'entry_field': None}),
    (ku.InfoKEGGurl, r.KEGGrest.info, {'database_name': 'pathway'}),
    (ku.KeywordsFindKEGGurl, r.KEGGrest.keywords_find, {'database_name': '', 'keywords': ['a', 'b']}),
    (
        ku.MolecularFindKEGGurl, r.KEGGrest.molecular_find,
        {'database_name': '', 'formula': 'abc', 'exact_mass': None, 'molecular_weight': None}
    ),
    (ku.DatabaseConvKEGGurl, r.KEGGrest.database_conv, {'kegg_database_name': 'a', 'outside_database_name': 'b'}),
    (ku.EntriesConvKEGGurl, r.KEGGrest.entries_conv, {'target_database_name': 'module', 'entry_ids': ['123', 'abc']}),
    (ku.DatabaseLinkKEGGurl, r.KEGGrest.database_link, {'target_database_name': 'x', 'source_database_name': 'y'}),
    (ku.EntriesLinkKEGGurl, r.KEGGrest.entries_link, {'target_database_name': '123', 'entry_ids': ['x', 'y']}),
    (ku.DdiKEGGurl, r.KEGGrest.ddi, {'drug_entry_ids': ['1', '2']})
]
@pt.mark.parametrize('KEGGurl,method,kwargs', test_rest_data)
def test_rest_method(mocker, KEGGurl, method, kwargs):
    kegg_rest = r.KEGGrest()
    request_spy = mocker.spy(kegg_rest, 'request')
    create_url_spy = mocker.spy(r.KEGGrest, '_get_kegg_url')
    kegg_url_mock = mocker.MagicMock()
    KEGGurlMock: mocker.MagicMock = mocker.patch(f'kegg_pull.rest.ku.{KEGGurl.__name__}', return_value=kegg_url_mock)
    getmro_mock: mocker.MagicMock = mocker.patch(f'kegg_pull.rest.ins.getmro', return_value={ku.AbstractKEGGurl})
    mocker.patch('kegg_pull.rest.rq.get', return_value=mocker.MagicMock(status_code=200))
    kegg_response = method(self=kegg_rest, **kwargs)
    request_spy.assert_called_once_with(KEGGurl=KEGGurlMock, **kwargs)
    create_url_spy.assert_called_once_with(KEGGurl=KEGGurlMock, kegg_url=None, **kwargs)
    KEGGurlMock.assert_called_once_with(**kwargs)
    getmro_mock.assert_called_once_with(KEGGurlMock)

    assert create_url_spy.spy_return == kegg_url_mock
    assert request_spy.spy_return == kegg_response
    assert kegg_response.kegg_url == kegg_url_mock


test_get_kegg_url_exception_data = [
    (
        {'KEGGurl': None, 'kegg_url': None},
        'Either an instantiated kegg_url object must be provided or an extended class of AbstractKEGGurl along with the'
        ' corresponding kwargs for its constructor.'
    ),
    (
        {'KEGGurl': r.KEGGrest, 'kegg_url': None},
        'The value for KEGGurl must be an inherited class of AbstractKEGGurl. The class "KEGGrest" is not.'
    )
]
@pt.mark.parametrize('kwargs,expected_message', test_get_kegg_url_exception_data)
def test_get_kegg_url_exception(kwargs: dict, expected_message: str):
    with pt.raises(ValueError) as error:
        r.KEGGrest._get_kegg_url(**kwargs)

    u.assert_expected_error_message(expected_message=expected_message, error=error)


def test_get_kegg_url_warning(mocker, caplog):
    kegg_url_mock = mocker.MagicMock()
    kegg_url = r.KEGGrest._get_kegg_url(KEGGurl=ku.InfoKEGGurl, kegg_url=kegg_url_mock, database_name='database mock')

    u.assert_warning(
        message='Both an instantiated kegg_url object and KEGGurl class are provided. Using the instantiated object...',
        caplog=caplog
    )

    assert kegg_url == kegg_url_mock
