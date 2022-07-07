from src.kegg_pull.kegg_url import ListKEGGurl
from src.kegg_pull.pull_single_from_kegg import pull_single_from_kegg


# TODO: Test a failure
# TODO: Test a Timeout
def test_pull_single_from_kegg(mocker):
    mock_get_return_value = mocker.MagicMock(status_code=200)
    mock_get = mocker.patch('src.kegg_pull.pull_single_from_kegg.get', return_value=mock_get_return_value)
    list_url = ListKEGGurl(database_type='organism')
    pull_single_from_kegg(kegg_url=list_url)
    mock_get.assert_called_once_with(list_url.url, timeout=60)
