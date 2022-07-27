import kegg_pull.web_request as wr


# TODO: Test timeout (e.g. mock sleep and assert called with sleep time)
# TODO: Test failed response (e.g. mock get to return non-200 status code and assert get called n_tries times
# TODO: Test _validate of web response and web request
def test_web_request(mocker):
    web_request = wr.WebRequest()
    mock_text = 'mock text'
    mock_content = b'mock content'
    mock_res = mocker.MagicMock(text=mock_text, content=mock_content, status_code=200)
    mock_get: mocker.MagicMock = mocker.patch('kegg_pull.web_request.rq.get', return_value=mock_res)
    mock_url = 'mock url'
    web_response: wr.WebResponse = web_request.get(url=mock_url)
    mock_get.assert_called_once_with(url=mock_url, timeout=60)

    assert web_response.status == wr.WebResponse.Status.SUCCESS
    assert web_response.text_body == mock_text
    assert web_response.binary_body == mock_content
