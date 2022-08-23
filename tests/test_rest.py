import pytest as pt

import kegg_pull.rest as r
import kegg_pull.kegg_url as ku
import requests as rq
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
    mock_text = 'mock text'
    mock_content = b'mock content'
    mock_response = mocker.MagicMock(text=mock_text, content=mock_content, status_code=200)
    mock_get: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.get', return_value=mock_response)
    mock_url = 'mock url'
    mock_kegg_url = mocker.MagicMock(url=mock_url)
    create_url_spy = mocker.spy(r.KEGGrest, '_get_kegg_url')
    kegg_response: r.KEGGresponse = kegg_rest.request(kegg_url=mock_kegg_url)
    create_url_spy.assert_called_once_with(KEGGurl=None, kegg_url=mock_kegg_url)
    mock_get.assert_called_once_with(url=mock_url, timeout=60)

    assert kegg_response.status == r.KEGGresponse.Status.SUCCESS
    assert kegg_response.text_body == mock_text
    assert kegg_response.binary_body == mock_content
    assert kegg_response.kegg_url == mock_kegg_url

    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.head', return_value=mock_response)
    success: bool = kegg_rest.test(kegg_url=mock_kegg_url)
    head_mock.assert_called_once_with(url=mock_url, timeout=60)

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
    mock_argv = ['kegg_pull', 'rest']
    mock_argv.extend(args)
    mocker.patch('sys.argv', mock_argv)
    mock_text_body = 'mock response body'
    mock_kegg_response = mocker.MagicMock(status=r.KEGGresponse.Status.SUCCESS, text_body=mock_text_body)

    mock_rest_method: mocker.MagicMock = mocker.patch(
        f'kegg_pull.rest.KEGGrest.{rest_method}', return_value=mock_kegg_response
    )

    mock_print: mocker.MagicMock = mocker.patch('builtins.print')
    r.main()
    mock_rest_method.assert_called_once_with(**kwargs)
    mock_print.assert_called_once_with(mock_text_body)


test_rest_data = [
    (ku.ListKEGGurl, r.KEGGrest.list, {'database_name': 'module'}),
    (ku.EntriesConvKEGGurl, r.KEGGrest.entries_conv, {'target_database_name': 'module', 'entry_ids': ['123', 'abc']})
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


def test_get_kegg_url_exception():
    pass


def test_get_kegg_url_warning():
    pass

# TODO test the other API operation in the KEGGrest class
