import pytest as pt

import kegg_pull.kegg_request as kr
import kegg_pull.rest as r


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
        f'kegg_pull.rest.KEGGrestAPI.{rest_method}', return_value=mock_kegg_response
    )

    mock_print: mocker.MagicMock = mocker.patch('builtins.print')
    r.main()
    mock_rest_method.assert_called_once_with(**kwargs)
    mock_print.assert_called_once_with(mock_text_body)

# TODO test the KEGGrestAPI class
