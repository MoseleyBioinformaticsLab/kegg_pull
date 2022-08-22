import pytest as pt
import requests as rq

import tests.utils as u
import kegg_pull.kegg_request as kr


test_kegg_response_exception_data = [
    ({'status': None, 'kegg_url': None}, 'A status must be specified for the KEGG response'),
    (
        {'status': kr.KEGGresponse.Status.SUCCESS, 'kegg_url': None},
        'A KEGG response cannot be marked as successful if its response body is empty'
    )
]
@pt.mark.parametrize('kwargs,expected_message', test_kegg_response_exception_data)
def test_kegg_response_exception(kwargs: dict, expected_message: str):
    with pt.raises(ValueError) as error:
        kr.KEGGresponse(**kwargs)

    u.assert_expected_error_message(expected_message=expected_message, error=error)


def test_kegg_request_exception():
    with pt.raises(ValueError) as error:
        kr.KEGGrequest(n_tries=0)

    expected_message = '0 is not a valid number of tries to make a KEGG request.'
    u.assert_expected_error_message(expected_message=expected_message, error=error)


def test_kegg_request_success(mocker):
    kegg_request = kr.KEGGrequest()
    mock_text = 'mock text'
    mock_content = b'mock content'
    mock_response = mocker.MagicMock(text=mock_text, content=mock_content, status_code=200)
    mock_get: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.rq.get', return_value=mock_response)
    mock_url = 'mock url'
    mock_kegg_url = mocker.MagicMock(url=mock_url)
    kegg_response: kr.KEGGresponse = kegg_request.execute_api_operation(kegg_url=mock_kegg_url)
    mock_get.assert_called_once_with(url=mock_url, timeout=60)

    assert kegg_response.status == kr.KEGGresponse.Status.SUCCESS
    assert kegg_response.text_body == mock_text
    assert kegg_response.binary_body == mock_content
    assert kegg_response.kegg_url == mock_kegg_url

    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.rq.head', return_value=mock_response)
    success: bool = kegg_request.test(kegg_url=mock_kegg_url)
    head_mock.assert_called_once_with(url=mock_url, timeout=60)

    assert success == True


def test_kegg_request_failed(mocker):
    n_tries = 4
    kegg_request = kr.KEGGrequest(n_tries=4)
    url_mock = 'url mock'
    kegg_url_mock = mocker.MagicMock(url=url_mock)
    failed_status_code = 400
    response_mock = mocker.MagicMock(text='', content=b'', status_code=failed_status_code)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.rq.get', return_value=response_mock)
    kegg_response: kr.KEGGresponse = kegg_request.execute_api_operation(kegg_url=kegg_url_mock)
    get_mock.assert_has_calls(mocker.call(url=url_mock, timeout=60) for _ in range(n_tries))

    assert kegg_response.status == kr.KEGGresponse.Status.FAILED
    assert kegg_response.kegg_url == kegg_url_mock
    assert kegg_response.text_body is None
    assert kegg_response.binary_body is None

    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.rq.head', return_value=response_mock)
    success: bool = kegg_request.test(kegg_url=kegg_url_mock)
    head_mock.assert_has_calls(mocker.call(url=url_mock, timeout=60) for _ in range(n_tries))

    assert success == False


def test_kegg_request_timeout(mocker):
    n_tries = 2
    time_out = 30
    sleep_time = 10.5
    kegg_request = kr.KEGGrequest(n_tries=n_tries, time_out=time_out, sleep_time=sleep_time)
    url_mock = 'url mock'
    kegg_url_mock = mocker.MagicMock(url=url_mock)
    get_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.rq.get', side_effect=rq.exceptions.Timeout())
    sleep_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.t.sleep')
    kegg_response: kr.KEGGresponse = kegg_request.execute_api_operation(kegg_url=kegg_url_mock)
    get_mock.assert_has_calls(mocker.call(url=url_mock, timeout=time_out) for _ in range(n_tries))
    sleep_mock.assert_has_calls(mocker.call(sleep_time) for _ in range(n_tries))

    assert kegg_response.status == kr.KEGGresponse.Status.TIMEOUT
    assert kegg_response.kegg_url == kegg_url_mock
    assert kegg_response.text_body is None
    assert kegg_response.binary_body is None

    sleep_mock.reset_mock()
    head_mock: mocker.MagicMock = mocker.patch('kegg_pull.kegg_request.rq.head', side_effect=rq.exceptions.Timeout())
    success: bool = kegg_request.test(kegg_url=kegg_url_mock)
    head_mock.assert_has_calls(mocker.call(url=url_mock, timeout=time_out) for _ in range(n_tries))
    sleep_mock.assert_has_calls(mocker.call(sleep_time) for _ in range(n_tries))

    assert success == False
