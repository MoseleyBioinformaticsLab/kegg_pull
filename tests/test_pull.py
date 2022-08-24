import pytest as pt
import shutil as sh
import os
import zipfile as zf
import itertools as i

import kegg_pull.rest as r
import kegg_pull.pull as p
import tests.utils as u


@pt.fixture(name='output_dir_mock', params=['mock-dir/', 'mock.zip'])
def setup_and_teardown(request):
    # Setup
    output_dir_mock = request.param

    yield output_dir_mock

    # Tear down
    if output_dir_mock.endswith('.zip') and os.path.isfile(output_dir_mock):
        os.remove(output_dir_mock)
    else:
        sh.rmtree(output_dir_mock, ignore_errors=True)

# TODO: Test with non-None entry field
# TODO: Test with binary response and another single entry response
# TODO: Test with a mol and gene-related entry field (for different separators)
# TODO: Test not getting all the requested entries
# TODO: Test with timeout
# TODO: Test with failures (complete failure and partial failure)
pt.mark.parametrize('output_dir_mock', ['mock-dir/', 'mock.zip'], indirect='setup_and_teardown')
def test_single_pull(mocker, output_dir_mock):
    entry_ids_mock = ['abc', 'xyz', '123']
    expected_file_contents = [f'{entry_id_mock} content' for entry_id_mock in entry_ids_mock]
    text_body_mock = '///'.join(expected_file_contents) + '///'

    response_mock = mocker.MagicMock(
        text_body=text_body_mock, status=r.KEGGresponse.Status.SUCCESS,
        kegg_url=mocker.MagicMock(multiple_entry_ids=True, entry_ids=entry_ids_mock)
    )

    kegg_rest_mock = mocker.MagicMock(get=mocker.MagicMock(return_value=response_mock))
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)
    single_pull = p.SinglePull(output_dir=output_dir_mock)
    KEGGrestMock.assert_called_once_with()
    pull_result: p.PullResult = single_pull.pull(entry_ids=entry_ids_mock)
    kegg_rest_mock.get.assert_called_once_with(entry_ids=entry_ids_mock, entry_field=None)

    assert pull_result.successful_entry_ids == tuple(entry_ids_mock)
    assert pull_result.failed_entry_ids == ()
    assert pull_result.timed_out_entry_ids == ()

    for entry_id_mock, expected_file_content in zip(entry_ids_mock, expected_file_contents):
        expected_file = f'{entry_id_mock}.txt'

        if output_dir_mock.endswith('.zip'):
            with zf.ZipFile(output_dir_mock, 'r') as zip_file:
                actual_file_content: str = zip_file.read(expected_file).decode()
        else:
            expected_file: str = os.path.join(output_dir_mock, expected_file)

            with open(expected_file, 'r') as file:
                actual_file_content: str = file.read()

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

    entry_ids_mock = list(i.chain.from_iterable(expected_pull_calls))

    expected_successful_entry_ids = (
        'A0', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'B0', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
        'C0', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'D0'
    )

    expected_failed_entry_ids = ('A9', 'B9', 'C9', 'D1')
    expected_timed_out_entry_ids = ()
    single_pull_mock = PickleableSinglePullMock()

    if MultiplePull is p.SingleProcessMultiplePull:
        single_pull_mock.pull = mocker.spy(single_pull_mock, 'pull')

    multiple_pull = MultiplePull(single_pull=single_pull_mock, **kwargs)
    multiple_pull_result: p.PullResult = multiple_pull.pull(entry_ids=entry_ids_mock)

    assert multiple_pull_result.successful_entry_ids == expected_successful_entry_ids
    assert multiple_pull_result.failed_entry_ids == expected_failed_entry_ids
    assert multiple_pull_result.timed_out_entry_ids == expected_timed_out_entry_ids

    if MultiplePull is p.SingleProcessMultiplePull:
        actual_pull_calls = getattr(single_pull_mock.pull, 'call_args_list')

        for actual_calls, expected_calls in zip(actual_pull_calls, expected_pull_calls):
            assert actual_calls.kwargs == {'entry_ids': expected_calls}


class PickleableSinglePullMock:
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


def test_main_help(mocker):
    u.assert_main_help(mocker=mocker, module=p, subcommand='pull')


# TODO: Test --help and -h
# TODO: Test from entry ID file and entry ID string
# TODO: Test pull single
def test_main(mocker, _):
    database_mock = 'brite'
    mocker.patch('sys.argv', ['kegg_pull', 'pull', 'multiple', f'--database-name={database_mock}'])
    kegg_rest_mock = mocker.MagicMock()
    KEGGrestMock = mocker.patch('kegg_pull.pull.r.KEGGrest', return_value=kegg_rest_mock)
    single_pull_mock = mocker.MagicMock()
    SinglePullMock = mocker.patch('kegg_pull.pull.SinglePull', return_value=single_pull_mock)
    entry_ids_mock = ['1', '2', '3']
    entry_ids_getter_mock = mocker.MagicMock(from_database=mocker.MagicMock(return_value=entry_ids_mock))
    EntryIdsGetterMock = mocker.patch('kegg_pull.pull.ei.EntryIdsGetter', return_value=entry_ids_getter_mock)

    pull_result_mock = mocker.MagicMock(
        successful_entry_ids=('a', 'b', 'c', 'x'), failed_entry_ids=('y', 'z'), timed_out_entry_ids=()
    )

    pull_mock = mocker.patch('kegg_pull.pull.SingleProcessMultiplePull.pull', return_value=pull_result_mock)
    multiple_pull_mock = mocker.MagicMock(pull=pull_mock)

    SingleProcessMultiplePullMock = mocker.patch(
        'kegg_pull.pull.SingleProcessMultiplePull', return_value=multiple_pull_mock
    )

    p.main()
    KEGGrestMock.assert_called_once_with(n_tries=None, time_out=None, sleep_time=None)
    SinglePullMock.assert_called_once_with(output_dir='.', kegg_rest=kegg_rest_mock, entry_field=None)
    EntryIdsGetterMock.assert_called_once_with(kegg_rest=kegg_rest_mock)
    entry_ids_getter_mock.from_database.assert_called_once_with(database_name=database_mock)
    SingleProcessMultiplePullMock.assert_called_once_with(single_pull=single_pull_mock, force_single_entry=True)
    pull_mock.assert_called_once_with(entry_ids=entry_ids_mock)

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

    with open('pull-results.txt', 'r') as file:
        actual_pull_results = file.read()

        assert actual_pull_results == expected_pull_results
