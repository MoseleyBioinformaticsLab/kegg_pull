import pytest as pt

import kegg_pull.kegg_request as kr
import kegg_pull.rest as r
import kegg_pull.kegg_url as ku


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
    mock_kegg_response = mocker.MagicMock(status=kr.KEGGresponse.Status.SUCCESS, text_body=mock_text_body)

    mock_rest_method: mocker.MagicMock = mocker.patch(
        f'kegg_pull.rest.KEGGrest.{rest_method}', return_value=mock_kegg_response
    )

    mock_print: mocker.MagicMock = mocker.patch('builtins.print')
    r.main()
    mock_rest_method.assert_called_once_with(**kwargs)
    mock_print.assert_called_once_with(mock_text_body)


test_rest_data = [
    (ku.UrlType.LIST, r.KEGGrest.list, {'database_name': 'module'}),
    (ku.UrlType.ENTRIES_CONV, r.KEGGrest.entries_conv, {'target_database_name': 'module', 'entry_ids': ['123', 'abc']})
]
@pt.mark.parametrize('url_type,method,kwargs', test_rest_data)
def test_request(mocker, url_type, method, kwargs):
    kegg_rest = r.KEGGrest()
    kegg_url_mock = mocker.MagicMock()
    create_url_mock: mocker.MagicMock = mocker.patch('kegg_pull.rest.ku.create_url', return_value=kegg_url_mock)
    kegg_response_mock = mocker.MagicMock()

    execute_api_operation_mock: mocker.MagicMock = mocker.patch(
        'kegg_pull.rest.kr.KEGGrequest.execute_api_operation', return_value=kegg_response_mock
    )

    request_spy = mocker.spy(kegg_rest, 'request')
    kegg_response = method(self=kegg_rest, **kwargs)
    request_spy.assert_called_once_with(url_type=url_type, **kwargs)
    create_url_mock.assert_called_once_with(url_type=url_type, **kwargs)
    execute_api_operation_mock.assert_called_once_with(kegg_url=kegg_url_mock)

    assert request_spy.spy_return == kegg_response_mock
    assert kegg_response == kegg_response_mock

# TODO test the other API operation in the KEGGrest class
