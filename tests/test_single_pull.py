import kegg_pull.kegg_url as ku
import kegg_pull.single_pull as sp


# TODO: Test a failure
# TODO: Test a Timeout
def test_single_pull(mocker):
    res_status_code = 200
    mock_get_return_value = mocker.MagicMock(status_code=res_status_code)
    mock_get = mocker.patch('kegg_pull.single_pull.rq.get', return_value=mock_get_return_value)
    list_url = ku.ListKEGGurl(database_type='rclass')
    res = sp.single_pull(kegg_url=list_url)
    mock_get.assert_called_once_with(list_url.url, timeout=60)

    assert res.status_code == res_status_code
