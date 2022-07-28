import pytest as pt
import os
import shutil as sh

import kegg_pull.kegg_request as kr
import kegg_pull.pull as p
import kegg_pull.kegg_url as ku


@pt.fixture(name='mock_output_dir')
def setup_and_teardown():
    # Setup
    mock_output_dir = 'mock-dir/'

    yield mock_output_dir

    # Tear down
    sh.rmtree(mock_output_dir, ignore_errors=True)

# TODO: Test with non-None entry field
# TODO: Test with binary response and another single entry response
# TODO: Test with a mol and gene-related entry field (for different separators)
# TODO: Test not getting all the requested entries
# TODO: Test with timeout
# TODO: Test with failures (complete failure and partial failure)
def test_single_pull(mocker, mock_output_dir):
    mock_entry_ids = ['abc', 'xyz', '123']
    expected_file_contents = [f'{mock_entry_id} content' for mock_entry_id in mock_entry_ids]
    mock_text_body = '///'.join(expected_file_contents) + '///'
    mock_response = mocker.MagicMock(text_body=mock_text_body, status=kr.KEGGresponse.Status.SUCCESS)
    mock_get = mocker.MagicMock(return_value=mock_response)
    kegg_request = mocker.MagicMock(get=mock_get)
    single_pull = p.SinglePull(output_dir=mock_output_dir, kegg_request=kegg_request, entry_field=None)
    pull_result: p.PullResult = single_pull.pull(entry_ids=mock_entry_ids)
    expected_get_url = f'{ku.BASE_URL}/get/{"+".join(mock_entry_ids)}'
    mock_get.assert_called_once_with(url=expected_get_url)

    assert pull_result.successful_entry_ids == tuple(mock_entry_ids)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()

    for mock_entry_id, expected_file_content in zip(mock_entry_ids, expected_file_contents):
        expected_file: str = os.path.join(mock_output_dir, f'{mock_entry_id}.txt')

        with open(expected_file, 'r') as f:
            actual_file_content: str = f.read()

            assert actual_file_content == expected_file_content
