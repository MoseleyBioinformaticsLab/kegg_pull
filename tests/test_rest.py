import kegg_pull.kegg_request as kr
import kegg_pull.rest as r


# TODO test exceptions thrown with timeout and failed
# TODO test other API operations (probably with pt.mark.parametrize)
# TODO test saving to a file (check file saved with correct contents and use with pt.fixture to remove it)
# TODO test binary is True and saving binary file
# TODO test binary print warning
def test_main(mocker):
    mock_database = 'module'
    mocker.patch('sys.argv', ['kegg_pull', 'rest', 'list', mock_database])
    mock_text_body = 'mock response body'
    mock_kegg_response = mocker.MagicMock(status=kr.KEGGresponse.Status.SUCCESS, text_body=mock_text_body)
    mock_list: mocker.MagicMock = mocker.patch('kegg_pull.rest.KEGGrestAPI.list', return_value=mock_kegg_response)
    mock_print: mocker.MagicMock = mocker.patch('builtins.print')
    r.main()
    mock_list.assert_called_once_with(database_name=mock_database)
    mock_print.assert_called_once_with(mock_text_body)


# TODO test the KEGGrestAPI class