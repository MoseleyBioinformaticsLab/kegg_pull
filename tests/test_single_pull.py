from src.kegg_pull.kegg_url import ListKEGGurl
from src.kegg_pull.single_pull import single_pull


# TODO: Test a failure
# TODO: Test a Timeout
def test_single_pull(mocker):
    mock_get_return_value = mocker.MagicMock(status_code=200)
    mock_get = mocker.patch('src.kegg_pull.single_pull.get', return_value=mock_get_return_value)
    list_url = ListKEGGurl(database_type='rclass')
    single_pull(kegg_url=list_url)
    mock_get.assert_called_once_with(list_url.url, timeout=60)
