import kegg_pull.kegg_request as kr


# TODO: Test timeout (e.g. mock sleep and assert called with sleep time)
# TODO: Test failed response (e.g. mock get to return non-200 status code and assert get called n_tries times
# TODO: Test _validate of kegg response and kegg request
# TODO: Test the test method
def test_kegg_request(mocker):
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
