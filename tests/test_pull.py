import pytest as pt
import shutil as sh
import os
import zipfile as zf

import kegg_pull.kegg_request as kr
import kegg_pull.pull as p
import itertools as i


@pt.fixture(name='mock_output_dir', params=['mock-dir/', 'mock.zip'])
def setup_and_teardown(request):
    # Setup
    mock_output_dir = request.param

    yield mock_output_dir

    # Tear down
    if mock_output_dir.endswith('.zip') and os.path.isfile(mock_output_dir):
        os.remove(mock_output_dir)
    else:
        sh.rmtree(mock_output_dir, ignore_errors=True)

# TODO: Test with non-None entry field
# TODO: Test with binary response and another single entry response
# TODO: Test with a mol and gene-related entry field (for different separators)
# TODO: Test not getting all the requested entries
# TODO: Test with timeout
# TODO: Test with failures (complete failure and partial failure)
pt.mark.parametrize('mock_output_dir', ['mock-dir/', 'mock.zip'], indirect='setup_and_teardown')
def test_single_pull(mocker, mock_output_dir):
    mock_entry_ids = ['abc', 'xyz', '123']
    expected_file_contents = [f'{mock_entry_id} content' for mock_entry_id in mock_entry_ids]
    mock_text_body = '///'.join(expected_file_contents) + '///'

    mock_response = mocker.MagicMock(
        text_body=mock_text_body, status=kr.KEGGresponse.Status.SUCCESS,
        kegg_url=mocker.MagicMock(multiple_entry_ids=True, entry_ids=mock_entry_ids)
    )

    mock_kegg_rest = mocker.MagicMock(get=mocker.MagicMock(return_value=mock_response))
    MockKEGGrestAPI = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=mock_kegg_rest)
    single_pull = p.SinglePull(output_dir=mock_output_dir)
    MockKEGGrestAPI.assert_called_once_with(kegg_request=None)
    pull_result: p.PullResult = single_pull.pull(entry_ids=mock_entry_ids)
    mock_kegg_rest.get.assert_called_once_with(entry_ids=mock_entry_ids, entry_field=None)

    assert pull_result.successful_entry_ids == tuple(mock_entry_ids)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()

    for mock_entry_id, expected_file_content in zip(mock_entry_ids, expected_file_contents):
        expected_file = f'{mock_entry_id}.txt'

        if mock_output_dir.endswith('.zip'):
            with zf.ZipFile(mock_output_dir, 'r') as zip_file:
                actual_file_content: str = zip_file.read(expected_file).decode()
        else:
            expected_file: str = os.path.join(mock_output_dir, expected_file)

            with open(expected_file, 'r') as f:
                actual_file_content: str = f.read()

        assert actual_file_content == expected_file_content


test_multiple_pull_data = [(p.SingleProcessMultiplePull, {}), (p.MultiProcessMultiplePull, {'n_workers': 2})]

# TODO: Test with force_single_pull with an entry field that can have multiple entries
# TODO: Test with an entry field that can only have one entry without force_single_pull
@pt.mark.parametrize('MultiplePull,kwargs', test_multiple_pull_data)
def test_multiple_pull(mocker, MultiplePull: type, kwargs: dict):
    expected_pull_calls = [
        ['A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9'],
        ['B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9'],
        ['C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
        ['D0', 'D1']
    ]

    mock_entry_ids = list(i.chain.from_iterable(expected_pull_calls))

    expected_successful_entry_ids = (
        'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
        'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'D0'
    )

    expected_failed_entry_ids = ('A9', 'B9', 'C9', 'D1')
    expected_timed_out_entry_ids = ()
    mock_single_pull = PickleableMockSinglePull()

    if MultiplePull is p.SingleProcessMultiplePull:
        mock_single_pull.pull = mocker.spy(mock_single_pull, 'pull')

    multiple_pull = MultiplePull(single_pull=mock_single_pull, **kwargs)
    multiple_pull_result: p.PullResult = multiple_pull.pull(entry_ids=mock_entry_ids)

    assert multiple_pull_result.successful_entry_ids == expected_successful_entry_ids
    assert multiple_pull_result.failed_entry_ids == expected_failed_entry_ids
    assert multiple_pull_result.timed_out_entry_ids == expected_timed_out_entry_ids

    if MultiplePull is p.SingleProcessMultiplePull:
        actual_pull_calls = getattr(mock_single_pull.pull, 'call_args_list')

        for actual_calls, expected_calls in zip(actual_pull_calls, expected_pull_calls):
            assert actual_calls.kwargs == {'entry_ids': expected_calls}


class PickleableMockSinglePull:
    def __init__(self):
        self.entry_field = None

    @staticmethod
    def pull(entry_ids: list):
        successful_entry_ids: list = tuple(entry_ids[:-1])
        failed_entry_ids: list = tuple(entry_ids[-1:])
        single_pull_result = p.PullResult()
        setattr(single_pull_result, '_successful_entry_ids', successful_entry_ids)
        setattr(single_pull_result, '_failed_entry_ids', failed_entry_ids)
        setattr(single_pull_result, '_timed_out_entry_ids', ())

        return single_pull_result


@pt.fixture(name='_')
def teardown():
    yield

    os.remove('pull-results.txt')


# TODO: Test --help and -h
# TODO: Test from entry ID file and entry ID string
# TODO: Test pull single
def test_main(mocker, _):
    mock_database = 'brite'
    mocker.patch('sys.argv', ['kegg_pull', 'pull', 'multiple', f'--database-name={mock_database}'])
    mock_kegg_request = mocker.MagicMock()
    MockKEGGrequest = mocker.patch('kegg_pull.pull.kr.KEGGrequest', return_value=mock_kegg_request)
    mock_single_pull = mocker.MagicMock()
    MockSinglePull = mocker.patch('kegg_pull.pull.SinglePull', return_value=mock_single_pull)
    mock_entry_ids = ['1', '2', '3']
    mock_entry_ids_getter = mocker.MagicMock(from_database=mocker.MagicMock(return_value=mock_entry_ids))
    MockEntryIdsGetter = mocker.patch('kegg_pull.pull.ei.EntryIdsGetter', return_value=mock_entry_ids_getter)

    mock_pull_result = mocker.MagicMock(
        successful_entry_ids=('a', 'b', 'c', 'x'), failed_entry_ids=('y', 'z'), timed_out_entry_ids=()
    )

    mock_pull = mocker.patch('kegg_pull.pull.SingleProcessMultiplePull.pull', return_value=mock_pull_result)
    mock_multiple_pull = mocker.MagicMock(pull=mock_pull)

    MockSingleProcessMultiplePull = mocker.patch(
        'kegg_pull.pull.SingleProcessMultiplePull', return_value=mock_multiple_pull
    )

    p.main()
    MockKEGGrequest.assert_called_once_with(n_tries=None, time_out=None, sleep_time=None)
    MockSinglePull.assert_called_once_with(output_dir='.', kegg_request=mock_kegg_request, entry_field=None)
    MockEntryIdsGetter.assert_called_once_with(kegg_request=mock_kegg_request)
    mock_entry_ids_getter.from_database.assert_called_once_with(database_name=mock_database)
    MockSingleProcessMultiplePull.assert_called_once_with(single_pull=mock_single_pull, force_single_entry=True)
    mock_pull.assert_called_once_with(entry_ids=mock_entry_ids)

    expected_pull_results = '\n'.join([
        '### Successful Entry IDs ###',
        'a',
        'b',
        'c',
        'x',
        '### Failed Entry IDs ###',
        'y',
        'z',
        '### Timed Out Entry IDs ###\n'
     ])

    with open('pull-results.txt', 'r') as f:
        actual_pull_results = f.read()

        assert actual_pull_results == expected_pull_results
