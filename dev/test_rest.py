import pytest as pt
import requests as rq

import kegg_pull.rest as r
import kegg_pull.kegg_url as ku
import dev.utils as u


test_kegg_response_exception_data = [
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


def test_kegg_rest():
    kegg_rest = r.KEGGrest(n_tries=2, time_out=30, sleep_time=0.5)

    assert kegg_rest._n_tries == 2
    assert kegg_rest._time_out == 30
    assert kegg_rest._sleep_time == 0.5

    kegg_rest = r.KEGGrest(n_tries=None, time_out=None, sleep_time=None)

    assert kegg_rest._n_tries == 3
    assert kegg_rest._time_out == 60
    assert kegg_rest._sleep_time == 5.0


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
    failed_status_code = 403
    response_mock = mocker.MagicMock(text='', content=b'', status_code=failed_status_code)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.rq.get', return_value=response_mock)
    sleep_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.time.sleep')
    kegg_response: r.KEGGresponse = kegg_rest.request(kegg_url=kegg_url_mock)
    get_mock.assert_has_calls(mocker.call(url=url_mock, timeout=60) for _ in range(n_tries))
    sleep_mock.assert_has_calls(mocker.call(5.0) for _ in range(n_tries))

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
    sleep_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.time.sleep')
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


test_rest_method_data = [
    (ku.ListKEGGurl, r.KEGGrest.list, {'database': 'module'}),
    (ku.GetKEGGurl, r.KEGGrest.get, {'entry_ids': ['xyz'], 'entry_field': None}),
    (ku.InfoKEGGurl, r.KEGGrest.info, {'database': 'pathway'}),
    (ku.KeywordsFindKEGGurl, r.KEGGrest.keywords_find, {'database': '', 'keywords': ['a', 'b']}),
    (
        ku.MolecularFindKEGGurl, r.KEGGrest.molecular_find,
        {'database': '', 'formula': 'abc', 'exact_mass': None, 'molecular_weight': None}
    ),
    (ku.DatabaseConvKEGGurl, r.KEGGrest.database_conv, {'kegg_database': 'a', 'outside_database': 'b'}),
    (ku.EntriesConvKEGGurl, r.KEGGrest.entries_conv, {'target_database': 'module', 'entry_ids': ['123', 'abc']}),
    (ku.DatabaseLinkKEGGurl, r.KEGGrest.database_link, {'target_database': 'x', 'source_database': 'y'}),
    (ku.EntriesLinkKEGGurl, r.KEGGrest.entries_link, {'target_database': '123', 'entry_ids': ['x', 'y']}),
    (ku.DdiKEGGurl, r.KEGGrest.ddi, {'drug_entry_ids': ['1', '2']})
]
@pt.mark.parametrize('KEGGurl,method,kwargs', test_rest_method_data)
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
    kegg_url = r.KEGGrest._get_kegg_url(KEGGurl=ku.InfoKEGGurl, kegg_url=kegg_url_mock, database='database mock')

    u.assert_warning(
        message='Both an instantiated kegg_url object and KEGGurl class are provided. Using the instantiated object...',
        caplog=caplog
    )

    assert kegg_url == kegg_url_mock
