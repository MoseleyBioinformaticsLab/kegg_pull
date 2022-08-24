import pytest as pt
import requests as rq

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


# TODO test exceptions thrown with timeout and failed
# TODO test other API operations (probably with pt.mark.parametrize)
# TODO test saving to a file (check file saved with correct contents and use with pt.fixture to remove it)
# TODO test binary is True and saving binary file
# TODO test binary print warning
test_main_data = [
    ('list', ['list', 'module'], {'database_name': 'module'}),
    (
        'entries_conv', ['conv', '--conv-target=genes', 'eid1,eid2'],
        {'target_database_name': 'genes', 'entry_ids': ['eid1', 'eid2']}
    )
]
@pt.mark.parametrize('rest_method,args,kwargs', test_main_data)
def test_main(mocker, rest_method: str, args: list, kwargs: dict):
    argv_mock = ['kegg_pull', 'rest']
    argv_mock.extend(args)
    mocker.patch('sys.argv', argv_mock)
    text_body_mock = 'response body mock'
    kegg_response_mock = mocker.MagicMock(status=r.KEGGresponse.Status.SUCCESS, text_body=text_body_mock)

    rest_method_mock: mocker.MagicMock = mocker.patch(
        f'kegg_pull.rest.KEGGrest.{rest_method}', return_value=kegg_response_mock
    )

    print_mock: mocker.MagicMock = mocker.patch('builtins.print')
    r.main()
    rest_method_mock.assert_called_once_with(**kwargs)
    print_mock.assert_called_once_with(text_body_mock)


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

# TODO test the other API operation in the KEGGrest class
