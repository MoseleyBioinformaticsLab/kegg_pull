import pytest as pt
import os
import shutil as sh

import src.kegg_pull.kegg_url as ku
import src.kegg_pull.multiple_pull as mp


@pt.fixture
def setup_and_teardown():
    # Setup
    actual_urls_dir = 'actual_urls/'
    mock_output_dir = 'mock-dir/'
    os.mkdir(actual_urls_dir)

    yield actual_urls_dir, mock_output_dir

    # Tear down
    sh.rmtree(mock_output_dir, ignore_errors=True)
    sh.rmtree(actual_urls_dir, ignore_errors=True)

# TODO: Test not getting all the requested entries
# TODO: Test with timeout
# TODO: Test with failures
def test_multiple_pull(mocker, setup_and_teardown):
    actual_urls_dir, mock_output_dir = setup_and_teardown
    mock_get_urls, expected_successful_entry_ids = _mock_input_output()
    expected_urls = {url.url for url in mock_get_urls}

    mock_make_urls_from_entry_id_list = mocker.patch(
        'src.kegg_pull.multiple_pull.mu.make_urls_from_entry_id_list', return_value=mock_get_urls
    )

    def mock_single_pull(kegg_url: ku.AbstractKEGGurl):
        suffix = ' content\n///'
        res = f'{suffix}\n'.join(kegg_url.entry_ids) + suffix
        res = mocker.MagicMock(text=res)
        _save_actual_url(actual_url=kegg_url.url, actual_urls_dir=actual_urls_dir)

        return res

    mocker.patch(
        'src.kegg_pull.multiple_pull.sp.single_pull', wraps=mock_single_pull
    )

    mock_database_type = 'mock-database-type'

    successful_entry_ids, failed_entry_ids = mp.multiple_pull(
        output_dir=mock_output_dir, database_type=mock_database_type, n_workers=len(mock_get_urls)
    )

    _test_actual_urls(actual_urls_dir=actual_urls_dir, expected_urls=expected_urls)

    assert sorted(successful_entry_ids) == expected_successful_entry_ids
    assert failed_entry_ids == []

    actual_files = [os.path.join(mock_output_dir, saved_file) for saved_file in sorted(os.listdir(mock_output_dir))]
    expected_files = [os.path.join(mock_output_dir, f'{entry_id}.txt') for entry_id in expected_successful_entry_ids]

    assert actual_files == expected_files

    expected_file_contents = [f'{entry_id} content' for entry_id in expected_successful_entry_ids]

    for (actual_saved_file, expected_file_content) in zip(actual_files, expected_file_contents):
        with open(actual_saved_file, 'r') as f:
            actual_file_content = f.read()

            assert actual_file_content == expected_file_content

    mock_make_urls_from_entry_id_list.assert_called_once_with(
        force_single_entry=False, database_type=mock_database_type, entry_id_list_path=None, entry_field=None
    )

    # Since mock_single_pull is deep-copied by the multiprocessing, it's not counted in the code coverage
    # This is because the copy is ran instead of the original, so the lines of code in the definition are not covered
    # So we run it here to maximize code coverage and ensure our mocked function works properly
    _test_mock_single_pull(actual_urls_dir=actual_urls_dir, mock_single_pull=mock_single_pull, mocker=mocker)


def _mock_input_output() -> tuple:
    mock_entry_ids = [
        ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'],
        ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],
        ['C1', 'C2']
    ]

    mock_get_urls = [ku.GetKEGGurl(entry_ids=entry_ids) for entry_ids in mock_entry_ids]
    expected_successful_entry_ids = []

    for entry_ids in mock_entry_ids:
        expected_successful_entry_ids.extend(entry_ids)

    return mock_get_urls, expected_successful_entry_ids


def _save_actual_url(actual_url: str, actual_urls_dir: str):
    url_file_name = actual_url.split('/')[-1]
    url_file_path = os.path.join(actual_urls_dir, url_file_name)

    with open(url_file_path, 'w') as f:
        f.write(actual_url)

def _test_actual_urls(actual_urls_dir: str, expected_urls: set):
    actual_urls = set()

    for url_file in os.listdir(actual_urls_dir):
        file_path: str = os.path.join(actual_urls_dir, url_file)

        with open(file_path, 'r') as f:
            actual_url: str = f.read()
            actual_urls.add(actual_url)

    assert actual_urls == expected_urls


def _test_mock_single_pull(actual_urls_dir: str, mock_single_pull: callable, mocker):
    file_name = 'test+url'
    expected_test_url = f'https://{file_name}'
    kegg_url = mocker.MagicMock(url=expected_test_url, entry_ids=['1', '2'])
    actual_res = mock_single_pull(kegg_url=kegg_url)
    expected_res = '1 content\n///\n2 content\n///'

    assert actual_res.text == expected_res

    with open(os.path.join(actual_urls_dir, file_name), 'r') as f:
        actual_test_url: str = f.read()

        assert actual_test_url == expected_test_url
