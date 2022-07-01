from requests import Response

from src.kegg_pull.generic_kegg_url import GenericKEGGurl
from src.kegg_pull.pull_single_from_kegg import pull_single_from_kegg


def test_pull_single_from_kegg(mocker):
    mock_return_value: Response = Response()
    mock_return_value.status_code = 200
    get = mocker.patch('src.kegg_pull.pull_single_from_kegg.get', return_value=mock_return_value)
    list_url: str = GenericKEGGurl(kegg_api_operation='list', database_type='organism')
    pull_single_from_kegg(kegg_url=list_url)
    get.assert_called_once_with(list_url.url, timeout=60)
